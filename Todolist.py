"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
from logzero import logger
from pathlib import Path
from audiorecorder import audiorecorder
import streamlit as st
import config
import os


os.environ["PATH"] += os.pathsep + r"C:ffmpeg\ffmpeg\bin"
genai.configure(api_key=config.google_api_key)

def generate_response(query,model,audio=None):
    """
    Uses gemini api to generate a response based on input. 
    
    args:
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

    system_behavior = """ 
            You are a Smart Assistant designed to break down tasks for users based on the SMART framework for goals. 
            1. Asses if the user has given a goal and details adhering to the SMART framework.  
                a. If yes, then provide detailed, actionable steps first grouped by week, and further broken down by days tailored to each user's input.
                b. If not, then ask helping quertions to get additional context to make the goal fit the SMART framework. 
            2. If a question doesn't fit a task breakdown, return "Sorry, I can't help with this request."  
            """
    
    gen_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior)
    file_path = Path("audio").mkdir(parents=True, exist_ok=True)

    audio_input_on = st.toggle("record voice through mic")
    if audio_input_on:
        query = "Listen to audio prompt and answer."
        audio = audiorecorder("Click to record", "Click to stop recording")
        st.audio(audio.export().read())
        if audio:
            if st.button("Submit Response", type="primary"):
                generate_response(query=query, model=gen_model, audio=audio)
    else:
        input_query = st.text_area(label="Input your query here.", placeholder="Type your goal along with the timeline you're looking to achieve it. Being Specific helps for a detailed breakdown!")
        if st.button("Submit Response", type="primary"):
            generate_response(query=input_query, model=gen_model)
    
    if st.session_state['response']:
        st.markdown(st.session_state['response'].text)