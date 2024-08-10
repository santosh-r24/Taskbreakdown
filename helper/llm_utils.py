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
                You are a Smart Assistant designed to help users break down tasks and manage their goals using the SMART framework. You also have the ability to interact with external applications like Google Tasks through function calls.

                1. Assess if the user has given a goal and supporting details adhering to the SMART framework, along with a start and end date for the goal.
                    a. If yes, provide detailed, actionable steps first grouped by week, beginning from start_date to end_date, and further broken down by days tailored to the user's input.
                    b. If not, ask questions to gather additional context to ensure the goal fits the SMART framework. Ask about the time the user can dedicate to the goal and the level of support required.
                    
                2.Generate an appropriate function call if:
                a. If the user requests to sync/add/update tasks to Google Tasks, call the function `add_or_update_task_to_google_tasks`.
                    i. if the plan is present call the function directly. **DO NOT PROMPT FOR ADDITIONAL DETAILS FOR FUNCTION CALLING**.
                    ii. If the plan is missing, inform the user to generate the plan 1st. **DO NOT PROMPT FOR ADDITIONAL DETAILS FOR FUNCTION CALLING**.
                b. If the user requests for feedback on progress/fetch tasks, call the function `fetch_tasks_from_google_tasks`.
                    i. if the tasks are synced to google call the function directly use the date parameter if mentioned, else set date to None. **DO NOT PROMPT FOR ADDITIONAL DETAILS FOR FUNCTION CALLING**.
                    ii. If the tasks are not synced to google, inform the user to sync the tasks to google before attempting this. **DO NOT PROMPT FOR ADDITIONAL DETAILS FOR FUNCTION CALLING**

                4. If a function call returns an error or unexpected result, inform the user with a clear and helpful message, suggesting possible next steps or alternatives.
                5. If a plan is provided but not synced to google, let the user know they can sync to google tasks.
                6. If a question is irrelevant to the SMART framework and task breakdowns, politely respond, "Sorry, I can't help with this request.".
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
    
    summary_behavior = """
                You're a smart assistant that provides a summary of the conversation between the user, and model. 
                1. Provide summary, while keeping the contextual details, and quantitaive details in place. 
                2. Try to provide a summary under 500 words. Try not exceeding the limit.  
                """
    generation_config_summary = genai.GenerationConfig(temperature=0.25)
    generation_config_assistant = genai.GenerationConfig(temperature=0.25)
    generation_config_json = genai.GenerationConfig(temperature=0.3, response_mime_type="application/json")
    
    functions = {
        "fetch_tasks": utils.fetch_tasks_from_google_tasks,
        "add_or_update_task": utils.add_or_update_task_to_google_tasks
    }
    # tool_functions = [utils.fetch_tasks, utils.add_or_update_task]
    st.session_state['summary_model'] = genai.GenerativeModel('gemini-1.5-flash', system_instruction=summary_behavior, generation_config=generation_config_summary)
    st.session_state['chat_model'] = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior, generation_config=generation_config_assistant, tools=functions.values())
    st.session_state['plan_model']  = genai.GenerativeModel('gemini-1.5-flash', system_instruction=json_system_behavior, generation_config=generation_config_json)


def generate_plan_response(prompt:str, model:genai.GenerativeModel, db=None, cursor=None):
    messages = copy.deepcopy(st.session_state['messages'])
    messages.append({"role":"user", "parts": [prompt]})
    response = generate_response(messages, model, db=db, cursor=cursor)
    if not response.candidates:
        st.error("No response generated. Please try again.")
        return None
    response_text = response.candidates[0].content.parts[0].text
    return response_text

def parse_plan_response(response_text:str):
    try:
        response_json = json.loads(response_text)
        return response_json.get("plan", [])
    except json.JSONDecodeError as e:
        st.error("Failed to decode the response. Please try again.")
        logger.error("Failed to decode the response. Please try again.", exc_info=True)
        return []
    
def generate_response(messages:list, model:genai.GenerativeModel, max_tokens = 5000, db=None, cursor=None):
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
        with st.spinner("New Summary is being generated..."):
            summary = summarize_history(messages[-15:-5])
        timestamp = datetime.datetime.now()
        db_funcs.save_summary(cursor, db, st.session_state['user_info']['email'], summary, timestamp)
        utils.cached_get_latest_summary.clear()
        st.session_state['latest_summary'] = summary
        messages = [{"role": "model", "parts": [summary]}] + messages[-5:]
        st.session_state['messages'] = messages[-5:]
    messages = copy.deepcopy(messages)
    _append_conditional_messages(messages)
    response = model.generate_content(messages)
    candidate = response.candidates[0]
    logger.debug(f"candidate is -> {candidate}")

    function_call = None
    for part in candidate.content.parts:
        if hasattr(part, 'function_call'):
            function_call = part.function_call
            break

    _handle_llm_function_call(messages, function_call)
    return response

def _append_conditional_messages(messages):
    """
    appends extra metadata to the user's response, if appropriate conditions are fulfilled.
    """
    if st.session_state['start_date'] and st.session_state['end_date']:
        messages[-1]['parts'][0] += f"""\t start_date:{st.session_state['start_date'].strftime('%Y-%m-%d')}, end_date:{st.session_state['end_date'].strftime('%Y-%m-%d')}"""
    if st.session_state['start_time'] and st.session_state['end_time']:
        messages[-1]['parts'][0] += f"""\t start_time:{st.session_state['start_time'].strftime('%H-%M-%S')}, end_time:{st.session_state['end_time'].strftime('%H-%M-%S')}"""

    if st.session_state['plan']:
        messages[-1]['parts'][0] += f'\n The plan is: {st.session_state["plan"]}'
    else:
        messages[-1]['parts'][0] += f'\n No plan is generated'
        
    if not st.session_state['task_ids_generated']:
        messages[-1]['parts'][0] += f'\n Tasks not synced to google'
    
    if st.session_state['task_ids_generated']:
        messages[-1]['parts'][0] += f'\n Tasks are synced to google'
    
def _handle_llm_function_call(messages, function_call = None):
    """
    Handles function calls if content.parts contains it.
    """
    if function_call:
        logger.debug(f'response for function call: {function_call}')
        function_name = function_call.name
        function_args = function_call.args
        function_args_dict = utils.map_composite_to_dict(function_call.args)
        logger.debug(f'response for function args: {function_args}\n response for function dict {function_args_dict} type of this{type(function_args_dict)}')
        function_result = []
        # Call the corresponding function and get the result
        if function_name == "fetch_tasks_from_google_tasks":
            if st.session_state['task_ids_generated']:
                due_date = function_args_dict.get('due_date', None)
                logger.debug(f'parsed date = {due_date}')
                function_result.append(utils.fetch_tasks_from_google_tasks(due_date))
            else:
                function_result.append("No tasks are synced to google, please generate a plan by clicking the 'generate and view plan' and then try again")
        elif function_name == "add_or_update_task_to_google_tasks":
            function_result.append(utils.add_or_update_task_to_google_tasks())       
        else:
            logger.debug("Unknown function being hit")
            function_result.append({"error": "Unknown function"})

        function_response = {"role": "user", "parts": [{"text": str(function_result)}]}
        messages.append(function_response)
        final_response = st.session_state['chat_model'].generate_content(messages)
        logger.debug(f"final response = {final_response}")
        return final_response

def summarize_history(messages:list):
    """
    Summarizes the given messages to reduce token count, while maintaining context.

    args:
    messages: List of message objects to summarize
    """
    model = st.session_state['summary_model']
    summary_prompt = "Summarize the following conversation, while maintaing qunatitative specific details :\n"
    for message in messages:
        if message["role"] == "user":
            summary_prompt += f"user: {message['parts'][0]}\n"
        else:
            summary_prompt += f"model: {message['parts'][0]}\n"
    
    response = model.generate_content([{"role":"user", "parts": [summary_prompt]}])
    summary = response.candidates[0].content.parts[0].text
    return summary