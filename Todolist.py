"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
from logzero import logger
from pathlib import Path
from audiorecorder import audiorecorder
import streamlit as st
import config
import os
# import torch
# from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
# import numpy as np

os.environ["PATH"] += os.pathsep + r"C:ffmpeg\ffmpeg\bin"

def generate_response(query,model,audio=None):
    """
    Uses gemini api to generate a response based on input. 

    query: the query to the model based on the audio input.
    model: Generative Model to be used for the task. default = genai.GenerativeModel('gemini-1.5-flash').
    audio: task recorded as audio input for the breakdown, if audiorecoder is used. default = None.
    """
    if audio:
        audio.export("audio/audio.wav", format="wav")
        audio_query = genai.upload_file(path="audio/audio.wav", display_name="audio input query")
        response = model.generate_content([audio_query, query])
    else:
        response = model.generate_content(query)
    st.session_state['response'] = response

if __name__ == "__main__":
    if 'response' not in st.session_state:
        st.session_state['response'] = None
    st.header("AI-Powered To-Do List",  divider='rainbow')
    st.subheader("Audio Recorder")


    genai.configure(api_key=config.google_api_key)
    gen_model = genai.GenerativeModel('gemini-1.5-flash')
    file_path = Path("audio").mkdir(parents=True, exist_ok=True)
    

    audio_input_on = st.toggle("record voice through mic")
    if audio_input_on:
        query = "Listen to audio prompt and answer it in detail"
        audio = audiorecorder("Click to record", "Click to stop recording")
        st.audio(audio.export().read())
        if audio:
            if st.button("Submit Response", type="primary"):
                generate_response(query=query, model=gen_model, audio=audio)
    else:
        input_query = st.text_area(label="Input your query here.", placeholder="I want to run a 10K in 1hour, currently I run a 10K in 70mins. Give me a breakdown on training regimen, i have 1 month to my race")
        if st.button("Submit Response", type="primary"):
            generate_response(query=input_query, model=gen_model)
    
    if st.session_state['response']:
        st.markdown(st.session_state['response'].text)
