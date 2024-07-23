"""A LLM powered todolist agent, that breaks down tasks given by user."""
import google.generativeai as genai
from logzero import logger
import streamlit as st
import database_functions as db_funcs


def check_if_user_and_api_keys_are_set():
    if not st.session_state['user_info'] and st.session_state['gemini_api_key']:
        st.error("Please login and set your gemini key, before proceeding.") 
        st.stop()
    if 'user_info' and 'gemini_api_key' not in st.session_state:
        st.error("Please login and set your gemini key, before proceeding.") 
        st.stop()

def initialise_ui_layout():
    """
    Sets the initial UI display elements.
    """
    st.header("AI-Powered To-Do List")
    st.markdown(''' :blue-background[Tip: Type your goal along with the timeline you're looking to achieve it. Being Specific helps for a detailed breakdown!] ''')
    st.divider()

def initialise_setup():
    """
    Initializes resources (gemini model, database, and system behaviour), and loads previous chat history. 
    """
    genai.configure(api_key=st.session_state["gemini_api_key"])
    system_behavior = """ 
                You are a Smart Assistant designed to break down tasks for users based on the SMART framework for goals. 
                1. Asses if the user has given a goal and details adhering to the SMART framework.  
                    a. If yes, then provide detailed, actionable steps first grouped by week, and further broken down by days tailored to each user's input.
                    b. If not, then ask helping quertions to get additional context to make the goal fit the SMART framework. 
                2. If a question doesn't fit a task breakdown, return "Sorry, I can't help with this request."  
                """
    gen_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior)
    db, cursor = db_funcs.initialize_database()
    
    #initialising chat history and summary
    if 'display_messages' not in st.session_state:
        st.session_state['display_messages'] = []
        st.session_state['messages'] = []
        st.session_state['latest_summary'] = None

    # Load previous chat messages from the database
    if not st.session_state['display_messages']:
        entire_chat_messages = cached_get_user_chat_messages(st.session_state['user_info']['email'], None)
        st.session_state['display_messages'] = entire_chat_messages
    
    return gen_model, db, cursor

@st.cache_data
def cached_get_user_chat_messages(email: str, timestamp=None):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_user_chat_messages(cursor, email, timestamp)

@st.cache_data
def cached_get_latest_summary(email: str):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_latest_summary(cursor, email)

def generate_response(messages, model, max_tokens = 4000, db=None, cursor=None):
    """
    Uses gemini api to generate a response based on input. 
    
    args:
    messages: List of message objects for the conversation history.
    model: Generative Model to be used for the task. default = genai.GenerativeModel('gemini-1.5-flash').
    """
    token_count = model.count_tokens(messages).total_tokens
    logger.debug(f"token count: {token_count}")
    summary = st.session_state['latest_summary']
    if token_count < max_tokens:
        if summary:
            logger.debug(f"Latest summary is fetched with newer messages")
            messages = [{"role": "model", "parts": summary}] + messages
    else:
        logger.debug("Summarizing older messages to reduce token count.")
        summary = summarize_history(messages[-15:-5], model)
        db_funcs.save_summary(cursor, db, st.session_state['user_info']['email'], summary)
        st.session_state['latest_summary'] = summary
        messages = [{"role": "model", "parts": [summary]}] + messages[-5:]
        # when new summary is generated, st.session_state['messages'] contain only the 5 most recent messages
        st.session_state['messages'] = messages[-5:]
        
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
    check_if_user_and_api_keys_are_set()
    initialise_ui_layout()
    gen_model, db, cursor = initialise_setup()

    # if summary is present, st.session_state['messages'] only has newer messages after the timestamp
    summary, latest_summary_timestamp = cached_get_latest_summary(st.session_state['user_info']['email'])
    st.session_state['latest_summary'] = summary
    if summary:
        new_messages = cached_get_user_chat_messages(st.session_state['user_info']['email'], latest_summary_timestamp)
        st.session_state['messages'] = new_messages
    # if it's not present, all messages from display_messages are used as messages.
    else:
        st.session_state['messages'] = st.session_state['display_messages']

    # Displays all chat messages from history on app rerun
    for message in st.session_state['display_messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"][0])
    
    #FUNCTIONING
    # React to user input
    if prompt:= st.chat_input("Type down your query"):
        st.chat_message("user", avatar=st.session_state['user_info']['picture']).markdown(prompt)
        st.session_state['messages'].append({"role":"user", "parts": [prompt]})
        st.session_state['display_messages'].append({"role":"user", "parts": [prompt]})
        db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "user", prompt)
        
        response = generate_response(messages=st.session_state['messages'], model=gen_model, db=db, cursor=cursor)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        # Add assistant response to chat history
        st.session_state['messages'].append({"role":"model", "parts": [response.text]})
        st.session_state['display_messages'].append({"role":"model", "parts": [response.text]})
        db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "model", response.text)