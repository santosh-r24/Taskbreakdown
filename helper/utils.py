"""Contains utility functions"""
import random
import streamlit as st
import datetime
import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from logzero import logger

import helper.database_functions as db_funcs

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/tasks']

def initialize_variables():
    """
    initializes streamlit variables used in the session state
    """
    _initialize_api_key()
    st.session_state['start_date'] = None
    st.session_state['end_date'] = None
    st.session_state['start_time'] = None
    st.session_state['end_time'] = None
    st.session_state['display_messages'] = []
    st.session_state['messages'] = []
    st.session_state['latest_summary'] = None
    st.session_state['initialized'] = True
    st.session_state['chat_model'] = None
    st.session_state['plan_model'] = None
    st.session_state['plan'] = None
    st.session_state['task_ids_generated'] = False
    st.session_state['goal_title'] = None
    st.session_state['calendar_service'] = None
    st.session_state['timezone'] = None
    st.session_state['task_ids_generated'] = False
    st.session_state['goal_title'] = None
    st.session_state['calendar_service'] = None
    st.session_state['timezone'] = None
    st.session_state['rate_limit'] = st.secrets['message_rate_limit']
    st.session_state['timeframe'] = st.secrets['timeframe_in_mins']
    st.session_state['variables_initialised'] = True
    
def initialize_previous_messages():
    """
    initializes and loads user's previous messages.
    """
    if not st.session_state['display_messages']:
        st.session_state['display_messages'] = cached_get_user_chat_messages(st.session_state['user_info']['email'], None)
    
    if 'messages_loaded' not in st.session_state:
        with st.spinner("Fetching previous messages"):
            logger.info("Summary is being fetched")
            summary, latest_summary_timestamp = cached_get_latest_summary(st.session_state['user_info']['email'])
            st.session_state['latest_summary'] = summary
            if summary:
                new_messages = cached_get_user_chat_messages(st.session_state['user_info']['email'], latest_summary_timestamp)
                st.session_state['messages'] = new_messages
            else:
                st.session_state['messages'] = st.session_state['display_messages']
            st.session_state['messages_loaded'] = True
            logger.info(f"Messages are initialised for {st.session_state['user_info']['email']}")

def _initialize_api_key():
    """
    Randomly initialises api key.
    """
    st.session_state['rate_limit'] = st.secrets['message_rate_limit']
    st.session_state['timeframe'] = st.secrets['timeframe_in_mins']
    st.session_state['variables_initialised'] = True
    
    if not st.session_state['display_messages']:
        st.session_state['display_messages'] = cached_get_user_chat_messages(st.session_state['user_info']['email'], None)

@st.cache_data(show_spinner=False)
def cached_get_user_chat_messages(email: str, timestamp=None):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_user_chat_messages(cursor, email, timestamp)

@st.cache_data(show_spinner=False)
def cached_get_latest_summary(email: str):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_latest_summary(cursor, email)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_get_message_count(email, timeframe):
    """Cache function to fetch message count"""
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_message_count_within_timeframe(cursor, email, timeframe)

def check_if_user_loggedin():
    if 'user_info' not in st.session_state:
        st.error("Please login before proceeding.") 
        st.stop()

    if not st.session_state['user_info']:
        st.error("Please login, and wait for setup to be ready before proceeding.") 
        st.stop()
    
def initialise_ui_layout_todolist_page():
    """
    Sets the initial UI display of Todolist tab elements.
    """
    st.header("To-Do List Smart Assistant")
    st.markdown(''' :blue-background[Tip: Read How to Use menu to get a better understanding on how the assistant can help you!] ''')

    st.markdown(''' :blue-background[Tip: Read How to Use menu to get a better understanding on how the assistant can help you!] ''')
    col1, col2 = st.columns(2, gap="small", vertical_alignment="top")
    with col1:
        with st.popover("How to Use"):
            st.markdown('''
                        <div style="color: white;">
                        1. <b style="color: #1E90FF;">SMART Goals</b>: The assistant follows the <a href="https://www.atlassian.com/blog/productivity/how-to-write-smart-goals" style="color: #1E90FF;">SMART framework</a> to help define goals.<br>
                        2. <b style="color: #1E90FF;">Provide Details</b>: The more specific and detailed you are with your goals, the better the assistant can help create a personalized plan.<br>
                        3. <b style="color: #1E90FF;">General Goals</b>: If you're not sure about the details, start with a general goal, and the assistant will guide you with questions to get more context.<br>
                        4. <b style="color: #1E90FF;">Set Timeline Dates</b>: Use the sidebar to set the start and end dates for your goals to ensure the plan aligns with your schedule.<br>
                        5. <b style="color: #1E90FF;">Schedule Time</b>: Specify the amount of time you can dedicate each day to your goal. This helps in creating a realistic plan.<br>
                        6. <b style="color: #1E90FF;">View and Sync Plans</b>: Once you receive a plan from the assistant, Click 'generate and view plan' to view detailed plans. You can then choose to sync the plan to google calendar, and tasks.<br>
                        7. <b style="color: #1E90FF;">New Plans</b>: If you want to create a new, unrelated plan, delete the chat and summary and start afresh.<br>
                        </div>
                        ''', unsafe_allow_html=True)
    with col2:
        with st.popover("Additional Details"):
            st.markdown('''
                        <div style="color: white;">
                        1. <b style="color: #1E90FF;">Message Summary</b>: The assistant summarizes older messages after a certain period of interaction (about 3500 words). This helps keep the context concise and relevant.<br>
                        2. <b style="color: #1E90FF;">Check Summary</b>: You can toggle the summary button in the sidebar to see the latest summary generated by the assistant.<br>
                        3. <b style="color: #1E90FF;">Context Use</b>: If no summary is generated, the assistant uses all previous messages for context.<br>
                        4. <b style="color: #1E90FF;">Non-Editable Summary</b>: Currently, the summary generated by the assistant cannot be edited.<br>
                        5. <b style="color: #1E90FF;">Mandatory Timeline</b>: Setting timeline dates is mandatory to generate plans and sync them to your calendar.<br>
                        6. <b style="color: #1E90FF;">Chat Deletion</b>: Use the "Delete Chat" button in the sidebar to clear all chat interactions with the assistant. This will reset the context.<br>
                        7. <b style="color: #1E90FF;">Summary Deletion</b>: Use the "Delete Summary" button in the sidebar to clear all summaries generated by the assistant.<br>
                        8. <b style="color: #1E90FF;">Rate Limit</b>: You can send up to 10 messages to the assistant per hour. The message count resets every hour.<br>
                        </div>
                        ''', unsafe_allow_html=True)
    st.divider()

@st.dialog("Delete chat", width="small")
def delete_chat_records(cursor, connection):
    """
    Function to clear chat records from the user. This function is called when the Delete chat button is clicked.
    """
    st.warning("All chat records associated will be deleted!")
    st.write("Type '**delete chat**' to proceed")
    delete_check = st.text_input("Enter delete key")
    if st.button("Submit") and delete_check == "delete chat":
        db_funcs.delete_chat(cursor, connection, st.session_state['user_info']['email'])
        st.session_state['display_messages'] = []
        st.session_state['messages'] = []
        cached_get_user_chat_messages.clear()
        st.rerun()

@st.dialog("Delete summary", width="small")
def delete_summary_records(cursor, connection):
    """
    Function to clear summary maintained by the model. This function is called when the Delete summary button is clicked.
    """
    st.warning("All summaries associated will be deleted!")
    st.write("Type '**delete summary**' to proceed")
    delete_check = st.text_input("Enter delete key")
    if st.button("Submit") and delete_check == "delete summary":
        db_funcs.delete_summaries(cursor, connection, st.session_state['user_info']['email'])
        st.session_state['latest_summary'] = None
        cached_get_latest_summary.clear()
        st.rerun()

def get_calendar_service():
    creds = Credentials(
        token=st.session_state['credentials']['token'],
        refresh_token=st.session_state['credentials']['refresh_token'],
        token_uri=st.session_state['credentials']['token_uri'],
        client_id=st.secrets['google_oauth']['client_id'],
        client_secret=st.secrets['google_oauth']['client_secret'],
        scopes=SCOPES
    )
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        st.error(f'An error occurred: {error}')
        return None
      
def _get_tasks_service():
    creds = Credentials(
        token=st.session_state['credentials']['token'],
        refresh_token=st.session_state['credentials']['refresh_token'],
        token_uri=st.session_state['credentials']['token_uri'],
        client_id=st.secrets['google_oauth']['client_id'],
        client_secret=st.secrets['google_oauth']['client_secret'],
        scopes=SCOPES
    )
    try:
        service = build('tasks', 'v1', credentials=creds)
        return service
    except HttpError as error:
        st.error(f'An error occurred: {error}')
        return None

def map_composite_to_dict(map_composite):
    """
    Converts a MapComposite object to a dictionary.
    """
    result = {}
    for key, value in map_composite.items():
        if isinstance(value, str):
            result[key] = value
        elif isinstance(value, int) or isinstance(value, float) or isinstance(value, bool):
            result[key] = value
        elif hasattr(value, "string_value"):
            result[key] = value.string_value
        elif hasattr(value, "number_value"):
            result[key] = value.number_value
        elif hasattr(value, "bool_value"):
            result[key] = value.bool_value
        else:
            result[key] = str(value)
    return result

def fetch_tasks_from_google_tasks(due_date :str =None) -> list:
    """
    Fetches all tasks from user's default tasklist and optionally filters by due date.

    Args:
        due_date: date must be in YYYY-MM-DD format, if no date is provided, date is set to None and all tasks are fetched.
    Returns:
        A list of dictionaries containing:
        title: title of the task.
        due: the date when the task is due.
        task_status: status of the task, if not completed returns needsAction.
        notes: detailed description of the task, defaults to empty string.
        web_link: a web viewable link of the task, defaults to empty string.
    """
    tasks_service = _get_tasks_service()
    logger.debug("fetching tasks now")
    function_result = []
    if tasks_service:
        try:
            results = tasks_service.tasks().list(tasklist='@default', showHidden=True).execute()
            items = results.get('items', [])
            if due_date:
                items = [item for item in items if 'due' in item and item['due'][:10] == due_date]
            logger.debug(f"tasks are {items}")
            for item in items:
                function_result.append({'title': item['title'],
                                    'due': item['due'],
                                    'task_status': item['status'],
                                    'notes': item.get('notes', ''),
                                    'web_link': item.get('webViewLink', '')})
        except HttpError as error:
            st.error(f'An error occurred: {error}')
            function_result.append(f'An error occurred: {error}')
    return function_result
           
def add_or_update_task_to_google_tasks(dummy_arg: str = "") -> list:
    """
    Adds a new task or updates an existing one to google tasks to the user's default tasklist.
    Args:
        dummy_str: Just feed in a dummy string here, this is to bypass gemini's fuction declaration
    Returns:
        A list of dictionaries containing:
        title: contains title of the task.
        due: contains the date when the task is due.
        status: status of the task, if not completed returns needsAction.
        notes: detailed description of the task, defaults to empty string.
        web_link: a web viewable link of the task, defaults to empty string.
    """
    if not st.session_state.get('plan'):
        return ["No plan has been created, please generate a plan by clicking the 'Generate and View Plan' button."]
    
    logger.debug("inside the function")
    db, cursor = db_funcs.initialize_database()
    function_result = []
    existing_task_ids_in_db = db_funcs.fetch_task_ids(cursor, st.session_state['user_info']['email'])
    tasks_service = _get_tasks_service()
    for day in st.session_state['plan']:
        date_obj = datetime.datetime.strptime(day['date'], "%Y-%m-%d").date()
        time_obj = datetime.datetime.strptime(day['end_time'], "%H:%M:%S").time()
        due = datetime.datetime.combine(date_obj, time_obj).isoformat() + 'Z'
        existing_task_id = existing_task_ids_in_db.get(day['date'], None)
        task = {
            'title': st.session_state['goal_title'],
            'due': due,
        }
        if day['task']:
            task['notes'] = day['task']
        try:
            if existing_task_id:
                # Update the existing task
                result = tasks_service.tasks().patch(tasklist='@default', task=existing_task_id, body=task).execute()
                logger.debug("Update existing google tasks")
            else:
                # Add a new task
                result = tasks_service.tasks().insert(tasklist='@default', body=task).execute()
            function_result.append({'title': result['title'],
                                'due': result['due'],
                                'status': result['status'],
                                'notes': result.get('notes', ''),
                                'web_link': result.get('webViewLink', '')})
            db_funcs.save_task_ids(cursor, db, st.session_state['user_info']['email'], result['id'], date_obj)
            logger.debug("Saved and added to google tasks")
        except HttpError as error:
            logger.debug("error when syncing")
            function_result.append(f'An error occurred while adding/updating the task: {error}')
    st.session_state['task_ids_generated'] = True
    return function_result

def get_user_timezone(service):
    try:
        settings = service.settings().get(setting='timezone').execute()
        return settings['value']
    except HttpError as error:
        st.error(f'An error occurred: {error}')
        return 'UTC'

def _create_calendar_event(service, start_date, end_date, summary, description, timezone):
    """
    Creates a calendar event based on the detailed plan generated.
    Args:
        service: A Resource object with methods for interacting with the service
        start_date: start_date of the event
        end_date: end_date of the event 
        summary: summary of the plan for the day
        description: Description of the event
        timezone: timezone of the user.
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_date.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_date.isoformat(),
            'timeZone': timezone,
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event