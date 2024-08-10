import streamlit as st
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import google.oauth2.id_token
import os 
from logzero import logger

import helper.database_functions as db_funcs
import helper.utils as utils

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ['GOOGLE_CLIENT_ID'] = st.secrets['google_oauth']['client_id']

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": st.secrets["google_oauth"]["auth_uri"],
            "token_uri": st.secrets["google_oauth"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "redirect_uris": st.secrets["google_oauth"]["redirect_uris"]
        }
    },
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/tasks'],
    redirect_uri= st.secrets["google_oauth"]["redirect_uris"][0]
)

def google_oauth():
    authorization_url, state = flow.authorization_url(prompt='consent')
    st.session_state['state'] = state
    st.write(f"[Login with Google]({authorization_url})")

def process_callback():
    if 'code' in st.query_params.keys():
        code = st.query_params['code']
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            request = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                credentials._id_token, request, os.environ['GOOGLE_CLIENT_ID'], clock_skew_in_seconds=3)
            st.session_state['credentials'] = credentials_to_dict(credentials)
            return id_info
        except Exception as e:
            st.error(f"Error fetching token: {e}")
            return None
    return None

def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token, 'token_uri': credentials.token_uri, 'client_id': credentials.client_id, 'client_secret': credentials.client_secret, 'scopes': credentials.scopes}

def initial_display_elements():
    st.markdown("""
        <style>
            h2 {
                color: #1E90FF; /* Blue color for h2 headings */
            }
            h3 {
                color: #1E90FF; /* Blue color for h3 headings */
            }
            h4 {
                color: #1E90FF; /* Blue color for h3 headings */
            }
            p, li {
                color: #FFFFFF; /* White color for paragraph and list items */
            }
        </style>
        """, unsafe_allow_html=True)
    
    st.header("TaskBreakdown 📝", divider='rainbow')
    st.write("Break down your big goals into manageable steps")
    st.subheader("Break down your big goals into manageable steps")

    st.markdown("""
    ## About TaskBreakdown
    TaskBreakdown is a smart assistant designed to help you break down your long-term goals into manageable steps. Whether you're looking to lose weight, switch jobs, or achieve any other complex goal, TaskBreakdown provides a personalized plan tailored to your needs.

    #### What Can You Do with TaskBreakdown?
    - **Set Long-Term Goals**: Define your big goals and let the assistant help you break them down.
    - **Create Action Plans**: Get detailed, actionable steps to achieve your goals.
    - **Sync with Google Calendar**: Schedule your plan by syncing them with your Google Calendar.
    - **Sync Tasks with Google Tasks**: Seamlessly add or update tasks in your Google Tasks to keep track of tasks to complete on a day/day basis
    - **Sync with Google Calendar**: Schedule your tasks and stay on track by syncing them with your Google Calendar.
    - **Track Progress**: Use the structured plan to make tangible progress on your goals.

    #### Example Goals:
    - **Lose Weight**: "How can I lose weight?"
    - **Switch Jobs**: "How can I switch jobs in my industry but don't know where to start?"
    - **Run a Marathon**: "How do I prepare to run a marathon in six months?"
    - **Learn a New Skill**: "What steps should I take to learn Python programming?"
                """)
    
    st.markdown("""
    ## How to Begin:
    1. **Sign up as a tester**: Send a mail or contact me on Twitter to sign up as a tester. After confirmation from me, proceed with step 2.
    2. **Login with Google**: Use the "Login with Google" link below to authenticate your Google account with all the necessary permissions. Wait for the setup to be ready.
    3. **Navigate to the Todolist Tab**: Go to the Todolist tab using the side bar and read the How to Use pop down to get help with using the assistant.
    """)


if __name__ == "__main__":
    st.set_page_config(page_title='Taskbreakdown', page_icon='', initial_sidebar_state='expanded', layout='wide', menu_items={'Report a Bug':'https://forms.gle/C8Zv8hzvYhPPvDW16'})
    login_status_container = st.container()

@st.cache_data(show_spinner=False)
def get_cached_api_key(email:str):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_user_api_key(cursor, email)

if __name__ == "__main__":
    st.set_page_config(page_title='Taskbreakdown', page_icon='', initial_sidebar_state='expanded', layout='wide', menu_items={'Report a Bug':'https://forms.gle/C8Zv8hzvYhPPvDW16'})
    login_status_container = st.container()
    initial_display_elements()
    db, cursor = db_funcs.initialize_database()

    if 'user_info' not in st.session_state:
        st.session_state['credentials'] = None
        st.session_state['user_info'] = None
        st.session_state['variables_initialised'] = False

    if st.session_state['user_info']:
        if not db_funcs.is_user_present(cursor, st.session_state['user_info']['email']):
            db_funcs.save_user(cursor, db, st.session_state['user_info']['email'], st.session_state['user_info'].get('name', 'User'), st.session_state['user_info'].get('picture', ''))

        if not st.session_state['variables_initialised']:
            utils.initialize_variables()
            st.session_state['calendar_service'] = utils.get_calendar_service()
            st.session_state['timezone'] = utils.get_user_timezone(st.session_state['calendar_service'])
            st.session_state['task_ids_generated'] = db_funcs.check_if_google_tasks_are_created(cursor, st.session_state['user_info']['email'])
            st.session_state['plan'] = db_funcs.fetch_plan_if_generated(cursor, st.session_state['user_info']['email'])
            if st.session_state['plan']:
                first_entry = st.session_state['plan'][0]
                last_entry = st.session_state['plan'][-1]
                # Initialize the variables
                st.session_state['start_date'] = first_entry['date']
                st.session_state['end_date'] = last_entry['date']
                st.session_state['start_time'] = first_entry['start_time']
                st.session_state['end_time'] = first_entry['end_time']
        
        with login_status_container:
            st.success(f"Welcome {st.session_state['user_info']['name']}. Setup is ready! You can now head onto the Todolist tab, to talk to the assistant :)")
        st.toast("Setup Ready! You can now head onto the Todolist tab, to talk to the assistant :)")
        st.warning(body="You're not logged in, please login to use the assistant")

    if st.session_state['user_info']:
        if not db_funcs.is_user_present(cursor, st.session_state['user_info']['email']):
            db_funcs.save_user(cursor, db, st.session_state['user_info']['email'], st.session_state['user_info'].get('name', 'User'), st.session_state['user_info'].get('picture', ''))

        if not st.session_state['variables_initialised']:
            utils.initialize_variables()
            st.session_state['calendar_service'] = utils.get_calendar_service()
            st.session_state['timezone'] = utils.get_user_timezone(st.session_state['calendar_service'])
            st.session_state['task_ids_generated'] = db_funcs.check_if_google_tasks_are_created(cursor, st.session_state['user_info']['email'])
            st.session_state['plan'] = db_funcs.fetch_plan_if_generated(cursor, st.session_state['user_info']['email'])
            if st.session_state['plan']:
                first_entry = st.session_state['plan'][0]
                last_entry = st.session_state['plan'][-1]
                # Initialize the variables
                st.session_state['start_date'] = first_entry['date']
                st.session_state['end_date'] = last_entry['date']
                st.session_state['start_time'] = first_entry['start_time']
                st.session_state['end_time'] = first_entry['end_time']
        
        with login_status_container:
            st.success(f"Welcome {st.session_state['user_info']['name']}. Setup is ready! You can now head onto the Todolist tab, to talk to the assistant :)")
        st.toast("Setup Ready! You can now head onto the Todolist tab, to talk to the assistant :)")
        logger.info(f"Welcome {st.session_state['user_info']['name']} ")
    else:
        user_info = process_callback()
        if user_info:
            st.session_state['user_info'] = user_info
            st.info(f"You've logged in as {user_info['name']}")
            st.rerun()
        else:
            with login_status_container:
                st.warning(body="You're not logged in, please login to use the assistant")
                google_oauth()

    st.markdown("""
    ---
    **Need help? Contact support at [santoshramakrishnan24@gmail.com](mailto:santoshramakrishnan24@gmail.com) \
    Reach out to me on [Twitter](https://x.com/SantoshKutti24)**
    """)