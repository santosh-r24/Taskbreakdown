import streamlit as st
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import google.oauth2.id_token
import os 
from logzero import logger
import database_functions as db_funcs

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
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar'],
    redirect_uri= st.secrets["google_oauth"]["redirect_uris"][1]
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

def initial_display_elements():
    st.markdown("# Home 📝")
    st.sidebar.markdown("# Home 📝")
    st.subheader("Welcome! This is a smart assistant to help break down your big seemingly complex tasks, into smaller steps that makes it easier to build on each day!")
    
    st.markdown("""
    ## How to Use This Tool:
    1. **Sign up as a tester**: Send me a mail to sign up as a tester. After confirmation follow from step 2.  
    2. **Login with Google**: Use the button below to log in with your Google account.
    3. **Enter Gemini API Key**: After logging in, enter your Gemini API key. If you don't have one, follow these steps to get it:
       - Go to [Gemini Studio](https://aistudio.google.com/app/apikey) and sign up or log in.
       - Navigate to the API section in your account settings.
       - Generate a new API key and copy it.
    4. **Navigate to the Todolist Tab**: Once your API key is saved, go to the Todolist tab to start using the assistant.
    """)

@st.cache_data(show_spinner=False)
def get_cached_api_key(email:str):
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_user_api_key(cursor, email)

if __name__ == "__main__":
    initial_display_elements()
    db, cursor = db_funcs.initialize_database()

    if 'user_info' not in st.session_state:
        st.session_state['user_info'] = None
        st.session_state['gemini_api_key'] = None
        st.markdown(''' **You're not logged in, please login to use the assistant** ''')

    if st.session_state['user_info']:
        logger.debug(st.session_state['user_info'])
        if not db_funcs.is_user_present(cursor, st.session_state['user_info']['email']):
            db_funcs.save_user(cursor, db, st.session_state['user_info']['email'], st.session_state['user_info']['name'], st.session_state['user_info']['picture'])
    
        st.write(f"Welcome {st.session_state['user_info']['given_name']} ")
        
        Update_key = st.button(label="Update Gemini key")
        if Update_key:
            api_key_input = st.text_input("Enter your Gemini API Key", type="password")
            submit = st.button(label="Submit")
            if submit and api_key_input is not None:
                st.session_state['gemini_api_key'] = api_key_input
                db_funcs.save_user(cursor, db, st.session_state['user_info']['email'], st.session_state['user_info']['name'], st.session_state['user_info']['picture'], st.session_state['gemini_api_key'])
                st.write(f"API key saved successfully")
            else:
                st.write(f"API key can't be empty")
                logger.debug(st.session_state['gemini_api_key'])
                
            logger.debug(st.session_state['gemini_api_key'])
        api_key = get_cached_api_key(st.session_state['user_info']['email'])
        st.session_state['gemini_api_key'] = api_key
        logger.debug(f"api key = {api_key}")
        if st.session_state['gemini_api_key']:
            st.session_state['gemini_api_key'] = api_key
            st.write("API Key found and loaded")
            st.write("You can now head onto the Todolist tab, to talk to the assistant :)")    
    else:
        user_info = process_callback()
        if user_info:
            st.session_state['user_info'] = user_info
            st.write(f"You've logged in as {user_info['given_name']}")
            st.rerun()
        else:
            google_oauth()

    st.markdown("""
    ---
    **Need help? Contact support at [santoshramakrishnan24@gmail.com](mailto:santoshramakrishnan24@gmail.com) \
    Reach out to me on [Twitter](https://x.com/SantoshKutti24)**
    """)