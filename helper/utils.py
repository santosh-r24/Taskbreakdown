"""Contains utility functions"""
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from logzero import logger

import helper.database_functions as db_funcs

SCOPES = ['https://www.googleapis.com/auth/calendar']
def initialize_variables():
    """
    initializes streamlit variables used in the session state, and loads user messages.
    """
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

def check_if_user_and_api_keys_are_set():
    if not st.session_state['user_info'] and st.session_state['gemini_api_key']:
        st.error("Please login and set your gemini key, before proceeding.") 
        st.stop()
    if 'user_info' and 'gemini_api_key' not in st.session_state:
        st.error("Please login and set your gemini key, before proceeding.") 
        st.stop()

def initialise_ui_layout_todolist_page():
    """
    Sets the initial UI display of Todolist tab elements.
    """
    st.header("To-Do List Agent")
    st.markdown(''' :blue-background[Tip: Read the instructions to get a better understanding on how the tool can help you!] ''')
    with st.popover("Instructions"):
        st.markdown('''
                    1. The Agent follows the [SMART framework](https://www.atlassian.com/blog/productivity/how-to-write-smart-goals) to help define goals.
                    2. Being specific and giving supporting details will help to curate a personalised plan.
                    3. If you're unsure of the details, send a general goal, the agent will help you asking details for context.
                    4. Set Timeline dates, and schedule time to help create a more accurate timeline. 
                    5. Timelines **must** be set in order to generate plans, and to sync to calendar. 
                    6. The agent generates a summary of older messages every so often (after every 5000 Tokens), and preserves newer messages for precise context.
                    7. You can see if a summary has been generated, by toggling the summary button.
                    8. If a summary hasn't been generated, the agent uses all previous messages as context. 
                    9. Currently the summary can't be edited.
                    10. Currently, the agent doesn't store plans generated, or synced to calendar. 
                    11. The agent only *remembers* the latest summary (if present) and the messages post it.
                    12. :blue-background[Delete chat] in the side bar can be used to delete all chat interactions with the agent.
                    13. :blue-background[Delete summary] in the side bar, deletes all summaries.
                    ''')
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
    st.write("Type '**delete summary **' to proceed")
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

def get_user_timezone(service):
    try:
        settings = service.settings().get(setting='timezone').execute()
        return settings['value']
    except HttpError as error:
        st.error(f'An error occurred: {error}')
        return 'UTC'

def create_event(service, start_date, end_date, summary, description, timezone):
    """
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
    