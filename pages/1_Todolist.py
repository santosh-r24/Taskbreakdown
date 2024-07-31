"""Main layout of the Todolist tab."""
from logzero import logger
import streamlit as st
import datetime

import helper.utils as utils
import helper.llm_utils as llm_utils
import helper.database_functions as db_funcs

if 'initialized' not in st.session_state:
    st.session_state['initialized'] = False

def initialise_side_bar_components():
    """
    Contains components that are present in the side bar, apart from pages.
    """
    with st.sidebar:
        set_date = st.toggle(label="Set Timelines")
        if set_date:
            with st.spinner("Timeline is being updated.."):
                with st.container(border=True, height=200):
                    st.session_state['start_date'] = st.date_input("Start date")
                    st.session_state['end_date'] = st.date_input("End date")
            st.success(f"Timeline updated from {st.session_state['start_date']} to {st.session_state['end_date']}!")
        set_time = st.toggle(label="Schedule Time")
        if set_time:
            with st.spinner("Schedule is being updated.."):
                with st.container(border=True, height=200):
                    st.session_state['start_time'] = st.time_input("Set start time", datetime.time(0, 00))
                    st.session_state['end_time'] = st.time_input("Set end time", datetime.time(1, 00))
            st.success(f"Schedule updated from {st.session_state['start_time']} to {st.session_state['end_time']} !")
        check_summary = st.toggle("See the Summary so far")
        if check_summary:
            if st.session_state['latest_summary']:
                with st.container(height=400):
                    st.write(st.session_state['latest_summary'])
            else:
                st.write("Summary hasn't been generated so far, continue talking with the agent")

        if st.button("Reset chat", type="primary"):
            utils.delete_chat_records(cursor, db)
        if st.button("Reset summary", type="primary"):
            utils.delete_summary_records(cursor, db)

if __name__ == "__main__":
    # Run initialization only if not already initialized
    utils.check_if_user_and_api_keys_are_set()
    if not st.session_state['initialized']:
        utils.initialize_variables()
    utils.initialise_ui_layout_todolist_page()
    db, cursor = db_funcs.initialize_database()
    llm_utils.initialise_model_setup()
    initialise_side_bar_components()

    if 'messages_loaded' not in st.session_state:
        with st.spinner("Fetching previous messages"):
            logger.info("Summary is being fetched")
            summary, latest_summary_timestamp = utils.cached_get_latest_summary(st.session_state['user_info']['email'])
            st.session_state['latest_summary'] = summary
            if summary:
                new_messages = utils.cached_get_user_chat_messages(st.session_state['user_info']['email'], latest_summary_timestamp)
                st.session_state['messages'] = new_messages
            else:
                st.session_state['messages'] = st.session_state['display_messages']
            st.session_state['messages_loaded'] = True
            logger.info(f"Messages are initialised for {st.session_state['user_info']['email']}")
    # Displays all chat messages from history on app rerun
    for message in st.session_state['display_messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"][0])
    
    # React to user input
    if prompt:= st.chat_input("Type down your query"):
        message_count = utils.cached_get_message_count(st.session_state['user_info']['email'], datetime.timedelta(minutes=st.session_state['timeframe']))
        logger.debug(f"User{st.session_state['user_info']['name']} reached {message_count} messages")
        if message_count <= st.session_state['rate_limit']:
            st.chat_message("user", avatar=st.session_state['user_info']['picture']).markdown(prompt)
            if st.session_state['start_date'] and st.session_state['end_date']:
                prompt += f"""\tstart_date:{st.session_state['start_date'].strftime('%Y-%m-%d')}, end_date:{st.session_state['end_date'].strftime('%Y-%m-%d')}
                            """
            if st.session_state['start_time'] and st.session_state['end_time']:
                prompt += f"""\tstart_time:{st.session_state['start_time'].strftime('%H-%M-%S')}, end_time:{st.session_state['end_time'].strftime('%H-%M-%S')}"""
            # logger.debug(f"Appending user message: {prompt}")
            st.session_state['messages'].append({"role":"user", "parts": [prompt]})
            st.session_state['display_messages'].append({"role":"user", "parts": [prompt]})
            db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "user", prompt)
            with st.spinner("Generating response... please wait"):
                response = llm_utils.generate_response(messages=st.session_state['messages'], model=st.session_state['chat_model'], db=db, cursor=cursor)

            with st.chat_message("assistant"):
                st.markdown(response.text)
            # Add assistant response to chat history
            st.session_state['messages'].append({"role":"model", "parts": [response.text]})
            st.session_state['display_messages'].append({"role":"model", "parts": [response.text]})
            db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "model", response.text)
        else: 
            st.warning("Rate limit exceeded. Please try again later.")
