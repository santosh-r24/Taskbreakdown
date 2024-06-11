"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
from logzero import logger
from pathlib import Path
from audiorecorder import audiorecorder
import streamlit as st
import config
import os 

os.environ["PATH"] += os.pathsep + r"C:ffmpeg\ffmpeg\bin"
def ingest_query(query,model,sample_file):
    response = model.generate_content([sample_file, query])
    logger.info(response)
    return response

if __name__ == "__main__":
    genai.configure(api_key=config.google_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    file_path = Path("audio").mkdir(parents=True, exist_ok=True)
    st.title("Audio Recorder")
    audio = audiorecorder("Click to record", "Click to stop recording")
    if len(audio) > 0:
        st.audio(audio.export().read())
        audio.export("audio/audio.wav", format="wav")
        # st.button("Record audio", type="primary", on_click=record_audio(file_path))
        # input_file = Path("{file_path}/audio.wav")
        # sample_file = genai.upload_file(path=input_file, display_name="Sample audio")
        # user_audio_query = "Listen to the audio prompt, and answer it. The output response must be in markdown format"
        # input = st.text_area(label="Input your query here.", placeholder="Listen to audio prompt and answer it")
        # if input:
        #     response = ingest_query(input, model, sameple_file)
        #     st.markdown(response)
