"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
import pyaudio
import wave
from logzero import logger
from dataclasses import dataclass, asdict
from pathlib import Path
import streamlit as st 


@dataclass
class StreamParams:
    format: int = pyaudio.paInt16
    channels: int = 2
    rate: int = 44100
    frames_per_buffer: int = 1024
    input: bool = True
    output: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
    
class Recorder:
    """Recorder uses the blocking I/O facility from pyaudio to record sound
    from mic.

    Attributes:
        - stream_params: StreamParams object with values for pyaudio Stream
            object
    """
    def __init__(self, stream_params: StreamParams) -> None:
        self.stream_params = stream_params
        self._pyaudio = None
        self._stream = None
        self._wav_file = None

    def record(self, duration: int, save_path: str) -> None:
        """Record sound from mic for a given amount of seconds.

        :param duration: Number of seconds we want to record for
        :param save_path: Where to store recording
        """
        logger.info("Start recording...")
        self._create_recording_resources(save_path)
        self._write_wav_file_reading_from_stream(duration)
        self._close_recording_resources()
        logger.info("Stop recording")

    def _create_recording_resources(self, save_path: str) -> None:
        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(**self.stream_params.to_dict())
        self._create_wav_file(save_path)

    def _create_wav_file(self, save_path: str):
        self._wav_file = wave.open(save_path, "wb")
        self._wav_file.setnchannels(self.stream_params.channels)
        self._wav_file.setsampwidth(self._pyaudio.get_sample_size(self.stream_params.format))
        self._wav_file.setframerate(self.stream_params.rate)

    def _write_wav_file_reading_from_stream(self, duration: int) -> None:
        for _ in range(int(self.stream_params.rate * duration / self.stream_params.frames_per_buffer)):
            audio_data = self._stream.read(self.stream_params.frames_per_buffer)
            self._wav_file.writeframes(audio_data)

    def _close_recording_resources(self) -> None:
        self._wav_file.close()
        self._stream.close()
        self._pyaudio.terminate()

def ingest_query(query,model):
    response = model.generate_content([sample_file, query])
    logger.info(response)
    return response

if __name__ == "__main__":
    genai.configure(api_key="AIzaSyAEAi0ejXrOsg00oRULMISTpVhyzn18510")
    model = genai.GenerativeModel('gemini-1.5-flash')
    stream_params = StreamParams()
    recorder = Recorder(stream_params)
    file_path = Path("ToDoListAgent/audio").mkdir(parents=True, exist_ok=True)
    recorder.record(10, f"{file_path}/audio.wav")
    input_file = Path("{file_path}/audio.wav")
    sample_file = genai.upload_file(path=input_file, display_name="Sample audio")
    user_audio_query = "Listen to the audio prompt, and answer it in markdown format"
    
    input = st.text_area(label="Input your query here.", placeholder="Listen to audio prompt and answer it")

    if input:
        response = ingest_query(input, model)
        st.markdown(response)
