import streamlit as st
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import google.oauth2.id_token
import os 
import config
from logzero import logger
import database_functions as db_funcs

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ['GOOGLE_CLIENT_ID'] = config.client_id
flow = Flow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar'],
    redirect_uri='http://localhost:8501'
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
            return id_info
        except Exception as e:
            st.error(f"Error fetching token: {e}")
            return None
    return None

if __name__ == "__main__":
    st.markdown("# Home 📝")
    st.sidebar.markdown("# Home 📝")
    st.subheader("Welcome! This is a smart assistant to help break down your big seemingly complex tasks, into smaller steps that makes it easier to build on each day!")
    if 'user_info' not in st.session_state:
        st.session_state['user_info'] = None
        st.markdown(''' **You're not logged in, please login to use the assistant** ''')

    if st.session_state['user_info']:
        user_info = st.session_state['user_info']
        st.write(f"Welcome {user_info['given_name']} ")
        # db_funcs.save_user(cursor, sql_db, user_info['email'], user_info['name'], user_info['picture'])
        # user_id = db_funcs.get_user_id(cursor, user_info['email'])
        st.session_state['user_id'] = user_info['given_name']
        # st.session_state['db_conn'] = sql_db
        st.write("You can now head onto the Todolist tab, to talk to the assistant :)")
        # st.write(f"Redirecting to the task generation page...")
        # st.switch_page("pages/Todolist.py")
    else:
        user_info = process_callback()
        if user_info:
            st.session_state['user_info'] = user_info
            st.write(f"You've logged in as {user_info['given_name']}")
            st.rerun()
        else:
            google_oauth()