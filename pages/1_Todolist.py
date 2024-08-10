"""Main layout of the Todolist tab."""
from logzero import logger
import streamlit as st
import datetime

import helper.utils as utils
import helper.llm_utils as llm_utils
import helper.database_functions as db_funcs
import column_2

def initialise_side_bar_components():
    """
    Contains components that are present in the side bar, apart from pages.
    """
    with st.sidebar:

        date_markdown = '''
        Set the start and due dates for your training plan.
        '''.strip()
        set_date = st.toggle(label="Set Timelines :date:", help=date_markdown)
        if set_date:
            with st.spinner("Timeline is being updated.."):
                with st.container(border=True, height=200):
                    st.session_state['start_date'] = st.date_input("Start date", value=st.session_state['start_date'])
                    st.session_state['end_date'] = st.date_input("End date", value=st.session_state['end_date'])
            st.toast(f"Timeline updated from {st.session_state['start_date']} to {st.session_state['end_date']}!")
        
        time_markdown = '''Set the start and end time for you can allocate to train per your training plan.'''.strip()
        
        set_time = st.toggle(label="Schedule Time :timer_clock:", help=time_markdown)
        if set_time:
            with st.container(border=True, height=200):
                st.session_state['start_date'] = st.date_input("Start date", value=st.session_state['start_date'])
                st.session_state['end_date'] = st.date_input("End date", value=st.session_state['end_date'])
                st.toast(f"Timeline updated from {st.session_state['start_date']} to {st.session_state['end_date']}!")
    
        time_markdown = '''Set the start and end time for you can allocate to train per your training plan.'''.strip()
        
        set_time = st.toggle(label="Schedule Time :timer_clock:", help=time_markdown)
        if set_time:
            with st.spinner("Schedule is being updated.."):
                with st.container(border=True, height=200):
                    st.session_state['start_time'] = st.time_input("Set start time", value=st.session_state['start_time'])
                    st.session_state['end_time'] = st.time_input("Set end time", value=st.session_state['end_time'])
            st.toast(f"Schedule updated from {st.session_state['start_time']} to {st.session_state['end_time']} !")
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
    st.set_page_config(page_title='Todolist', page_icon=':memo:', initial_sidebar_state='expanded', layout='wide')
    utils.check_if_user_loggedin()
    utils.initialize_previous_messages()
    utils.initialise_ui_layout_todolist_page()
    db, cursor = db_funcs.initialize_database()
    llm_utils.initialise_model_setup()
    initialise_side_bar_components()
    col_1, col_2 = st.columns([0.7,0.3])
    
    # React to user input
    with col_1:
        st.subheader("SMART ASSISTANT")
        a = st.container(height=600)
        with a:
            for message in st.session_state['display_messages']:
                with st.chat_message(message["role"]):
                    st.markdown(message["parts"][0])

        if prompt:= st.chat_input("How do i train for a marathon in 6 months, i can run 3 days a week"):
            message_count = utils.cached_get_message_count(st.session_state['user_info']['email'], datetime.timedelta(minutes=st.session_state['timeframe']))
            logger.debug(f"User {st.session_state['user_info']['name']} reached {message_count} messages")
            if message_count <= st.session_state['rate_limit']:
                with a:
                    st.chat_message("user").markdown(prompt)
                st.session_state['messages'].append({"role":"user", "parts": [prompt]})
                st.session_state['display_messages'].append({"role":"user", "parts": [prompt]})
                db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "user", prompt)
                with st.spinner("Generating response... please wait"):
                    response = llm_utils.generate_response(messages=st.session_state['messages'], model=st.session_state['chat_model'], db=db, cursor=cursor)
                with a:
                    with st.chat_message("assistant"):
                        st.markdown(response.text)
                # Add assistant response to chat history
                st.session_state['messages'].append({"role":"model", "parts": [response.text]})
                st.session_state['display_messages'].append({"role":"model", "parts": [response.text]})
                db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "model", response.text)
            else: 
                st.toast("Rate limit of 10 exceeded. Please try again later.")
    with col_2:
        column_2._contents_of_column_2(db,cursor)
    logger.debug(f"tasks are generated: {st.session_state['task_ids_generated']}")
    logger.debug(f"st.session_state['goal_title'] = {st.session_state['goal_title']}")
    col_1, col_2 = st.columns([0.7,0.3])
    
    # React to user input
    with col_1:
        st.subheader("SMART ASSISTANT")
        a = st.container(height=600)
        # Displays all chat messages from history on app rerun
        with a:
            for message in st.session_state['display_messages']:
                with st.chat_message(message["role"]):
                    st.markdown(message["parts"][0])

        # with st.container():
        if prompt:= st.chat_input("How do i train for a marathon in 6 months, i can run 3 days a week"):
            message_count = utils.cached_get_message_count(st.session_state['user_info']['email'], datetime.timedelta(minutes=st.session_state['timeframe']))
            logger.debug(f"User {st.session_state['user_info']['name']} reached {message_count} messages")
            if message_count <= st.session_state['rate_limit']:
                with a:
                    st.chat_message("user").markdown(prompt) #st.session_state['user_info']['picture']
                st.session_state['messages'].append({"role":"user", "parts": [prompt]})
                st.session_state['display_messages'].append({"role":"user", "parts": [prompt]})
                db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "user", prompt)
                with st.spinner("Generating response... please wait"):
                    response = llm_utils.generate_response(messages=st.session_state['messages'], model=st.session_state['chat_model'], db=db, cursor=cursor)
                with a:
                    with st.chat_message("assistant"):
                        st.markdown(response.text)
                # Add assistant response to chat history
                st.session_state['messages'].append({"role":"model", "parts": [response.text]})
                st.session_state['display_messages'].append({"role":"model", "parts": [response.text]})
                db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "model", response.text)
            else: 
                st.toast("Rate limit of 10 exceeded. Please try again later.")
    with col_2:
        column_2._contents_of_column_2(db,cursor)
        
    logger.debug(f"tasks are generated: {st.session_state['task_ids_generated']}")
    logger.debug(f"st.session_state['goal_title'] = {st.session_state['goal_title']}")