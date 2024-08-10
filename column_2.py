"""Contains layout and functions for generating a plan, and sending the plan to the calander."""
import streamlit as st
from logzero import logger
import datetime

import helper.llm_utils as llm_utils
import helper.utils as utils
import helper.database_functions as db_funcs
    

def _contents_of_column_2(db, cursor):
    """
    Contains functions and layout for the 2nd column displayed on Todolist Tab.
    """
    st.subheader("Generate Detailed plan")

    if not all([st.session_state['start_date'], 
    st.session_state['end_date'],
    st.session_state['start_time'],
    st.session_state['end_time']]):
        st.warning(icon="🚨", body="Ensure Timelines are set, and times are scheduled in the sidebar")
        st.stop()
    
    st.info("Click Generate plan, to view the structure of the plan on a day to day basis.")
    
    if st.button("Generate and View plan"):
        prompt = f"Using the previous messages as context. Generate a detailed plan starting from date {st.session_state['start_date']} to {st.session_state['end_date']} scheduled each day from start_time {st.session_state['start_time']} to {st.session_state['end_time']}"
        with st.spinner('Generating Plan... please wait'):
            response_text = llm_utils.generate_plan_response(prompt, st.session_state['plan_model'], db, cursor)
            st.session_state['plan'] = llm_utils.parse_plan_response(response_text)
            db_funcs.save_plan(cursor, db, st.session_state['user_info']['email'], st.session_state['plan'])
            st.toast("The plan is generated, you can now talk to the agent, and sync your plans to calendar, and google tasks!")
            logger.debug(f"The plan for user {st.session_state['user_info']['email']} looks like this\n {st.session_state['plan']}")
    
    if st.session_state['plan']:
        st.toast("Plan has been generated")
        st.session_state['goal_title'] = st.session_state['plan'][0]['goal']
        with st.container(height=300):
            st.json(st.session_state['plan'], expanded=True)
        logger.debug(f"The plan has been printed")

    st.subheader("SYNC PLANS TO GOOGLE")
    st.info("Click Send to Calendar, for the plan to be synced to calendar.")
    if st.button("Send plan to Calendar :spiral_calendar_pad:"):
        with st.spinner("Syncing plan to Calendar..."):
            service = utils.get_calendar_service()
            if service:
                timezone = utils.get_user_timezone(service)
                st.write(f"Your timezone is: {timezone}")
                logger.debug(f"The plan is synced to calendar")
                for day in st.session_state['plan']:
                    start_datetime = datetime.datetime.strptime(f"{day['date']} {day['start_time']}", "%Y-%m-%d %H:%M:%S")
                    end_datetime = datetime.datetime.strptime(f"{day['date']} {day['end_time']}", "%Y-%m-%d %H:%M:%S")
                    calendar_event = utils._create_calendar_event(
                        service,
                        start_datetime,
                        end_datetime,
                        day["goal"],
                        day["task"],
                        timezone)
                    st.write(f"Event created: {calendar_event.get('htmlLink')}")
