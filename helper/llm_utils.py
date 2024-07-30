"""Contains Functions with regards to the gemini model"""
import copy
import datetime
import json
import streamlit as st
import google.generativeai as genai
from logzero import logger

import helper.database_functions as db_funcs
import helper.utils as utils


def initialise_model_setup():
    """
    Initializes resources that are required by the gen ai (gemini) model gemini. 
    """
    genai.configure(api_key=st.session_state["gemini_api_key"])
    system_behavior = """ 
                You are a Smart Assistant designed to break down tasks for users based on the SMART framework for goals. 
                1. Asses if the user has given a goal and supporting details adhering to the SMART framework, along with a start and end date for the goal.  
                    a. If yes, then provide detailed, actionable steps first grouped by week begininning from start_date to end_date, and further broken down by days tailored to user's input.
                    b. If not, then ask helping quertions to get additional context to make the goal fit the SMART framework, ask the amount of time the user can spend on the goal, and level of support required.
                2. If start_date is specified, always start the plan from the specified start_date, not from the beginning of the week. Ensure the plan aligns with the actual days of the week starting from start_date.
                3. If start_time and end_time is specified, then that is the time the user can allocate each day for the task. Ensure the plan aligns with the time duration specified.
                4. Do not generate a plan unless you have sufficient details about the user and their goal. Do not assume anything about the user, unless specified.
                5. If a question doesn't fit a task breakdown, return "Sorry, I can't help with this request."
                """
    
    json_system_behavior = """
                You are a Smart Assistant designed to generate a plan for users based on the SMART framework for goals, using the context of messages provided.
                1. Do not leave out any details in the messages.
                2. Use the exact details as provided in the chat between the user and model.
                3. Do not assume anything that is not provided in the messages.
                4. The "date" field for the plan MUST always be start at the start_date and end at end_date specified.
                5. The time duration for each day must be between the start_time and end_time specified.
                6. When generating a plan, provide the output in the following JSON format:
                   {"plan": [{"date": "YYYY-MM-DD", "task": "Detailed Task description", "goal": "Goal description", "start_time":"start time duration", "end_time": "end time duration"}, ...]}
                """
    generation_config = genai.GenerationConfig(temperature=0.5)
    generation_config_json = genai.GenerationConfig(temperature=0.3, response_mime_type="application/json")
    st.session_state['chat_model'] = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior, generation_config=generation_config)
    st.session_state['plan_model']  = genai.GenerativeModel('gemini-1.5-flash', system_instruction=json_system_behavior, generation_config=generation_config_json)

def generate_plan_response(prompt:str, model:genai.GenerativeModel, db=None, cursor=None):
    messages = copy.deepcopy(st.session_state['messages'])
    messages.append({"role":"user", "parts": [prompt]})
    response = generate_response(messages, model, db=db, cursor=cursor)
    if not response.candidates:
        st.error("No response generated. Please try again.")
        return None
    response_text = response.candidates[0].content.parts[0].text
    # logger.debug(f"Response after mime is set: {response_text}")
    return response_text

def parse_plan_response(response_text:str):
    try:
        response_json = json.loads(response_text)
        return response_json.get("plan", [])
    except json.JSONDecodeError as e:
        # logger.debug(response_text)
        st.error("Failed to decode the response. Please try again.")
        logger.error("Failed to decode the response. Please try again.", exc_info=True)
        return []
    
def generate_response(messages:list, model:genai.GenerativeModel, max_tokens = 4000, db=None, cursor=None):
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
        st.info("New Summary is being generated...")
        summary = summarize_history(messages[-15:-5], model)
        timestamp = datetime.datetime.now()
        db_funcs.save_summary(cursor, db, st.session_state['user_info']['email'], summary, timestamp)
        utils.cached_get_latest_summary.clear()
        st.session_state['latest_summary'] = summary
        messages = [{"role": "model", "parts": [summary]}] + messages[-5:]
        # when new summary is generated, st.session_state['messages'] contain only the 5 most recent messages
        st.session_state['messages'] = messages[-5:]
    # logger.debug(f"\n messages are: {messages}")
    response = model.generate_content(messages)
    return response

def summarize_history(messages:list, model:genai.GenerativeModel):
    """
    Summarizes the given messages to reduce token count, while maintaining context.

    args:
    messages: List of message objects to summarize
    model: Generative Model used for summarizing. default = 'gemini-1.5-flash'
    """
    summary_prompt = "Summarize the following conversation in under 500 words, try to maintain exact specific details :\n"
    for message in messages:
        if message["role"] == "user":
            summary_prompt += f"user: {message['parts'][0]}\n"
        else:
            summary_prompt += f"model: {message['parts'][0]}\n"
    
    response = model.generate_content([{"role":"user", "parts": [summary_prompt]}])
    summary = response.candidates[0].content.parts[0].text
    return summary