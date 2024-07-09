"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
from logzero import logger
from pathlib import Path
import streamlit as st
import os
import database_functions as db_funcs


os.environ["PATH"] += os.pathsep + r"C:ffmpeg\ffmpeg\bin"

def generate_response(messages,model,audio=None, max_tokens = 4000):
    """
    Uses gemini api to generate a response based on input. 
    
    args:
    messages: List of message objects for the conversation history.
    model: Generative Model to be used for the task. default = genai.GenerativeModel('gemini-1.5-flash').
    audio: task recorded as audio input for the breakdown, if audiorecoder is used. default = None.
    """
    token_count = model.count_tokens(messages).total_tokens
    logger.debug(f"token count: {token_count}")
    if token_count > max_tokens:
        logger.debug(f"The message is being summarised")
        half_index = len(messages)//2
        summary =  summarize_history(messages[:half_index], model)
        messages = [{"role": "model", "parts": summary}] + messages[half_index:]
    
    response = model.generate_content(messages)
    return response

def summarize_history(messages, model):
    """
    Summarizes the given messages to reduce token count, while maintaining context.

    args:
    messages: List of message objects to summarize
    model: Generative Model used for summarizing. default = 'gemini-1.5-flash'
    """
    summary_prompt = "Summarize the following conversation:\n"
    for message in messages:
        if message["role"] == "user":
            summary_prompt += f"user: {message['parts'][0]}\n"
        else:
            summary_prompt += f"model: {message['parts'][0]}\n"
    
    response = model.generate_content([{"role":"user", "parts": [summary_prompt]}])
    summary = response.candidates[0].content.parts[0].text
    return summary

if __name__ == "__main__":
    st.header("AI-Powered To-Do List")
    st.markdown(''' :blue-background[Tip: Type your goal along with the timeline you're looking to achieve it. Being Specific helps for a detailed breakdown!] ''')
    st.divider()
    system_behavior = """ 
                You are a Smart Assistant designed to break down tasks for users based on the SMART framework for goals. 
                1. Asses if the user has given a goal and details adhering to the SMART framework.  
                    a. If yes, then provide detailed, actionable steps first grouped by week, and further broken down by days tailored to each user's input.
                    b. If not, then ask helping quertions to get additional context to make the goal fit the SMART framework. 
                2. If a question doesn't fit a task breakdown, return "Sorry, I can't help with this request."  
                """
    file_path = Path("audio").mkdir(parents=True, exist_ok=True)
    if 'user_info' and 'gemini_api_key' not in st.session_state:
        st.error("Please login and set your gemini key, before proceeding.")
        st.stop()
    else:
        genai.configure(api_key=st.session_state["gemini_api_key"])
        gen_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior)
        user_info = st.session_state['user_info']
        user_id = st.session_state['user_id']
        sql_db, cursor = db_funcs.initialize_database()
        # db_funcs.update_roles_in_database(cursor, sql_db)
        # db_funcs.view_first_few_rows()

        #initialising chat history
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
        
        # Load previous chat messages from the database
        if not st.session_state['messages']:
            chat_messages = db_funcs.get_user_chat_messages(cursor, user_id)
            st.session_state['messages'] = chat_messages
        
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["parts"][0])
        
        # React to user input
        if prompt:= st.chat_input("Type down your task"):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role":"user", "parts": [prompt]})
            db_funcs.save_chat_message(cursor, sql_db, user_id, "user", prompt)
            
            response = generate_response(messages=st.session_state['messages'], model=gen_model)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            # Add assistant response to chat history
            st.session_state['messages'].append({"role":"model", "parts": [response.text]})
            db_funcs.save_chat_message(cursor, sql_db, user_id, "model", response.text)