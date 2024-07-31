"""Contains layout and functions for generating a plan, and sending the plan to the calander."""
import streamlit as st
from logzero import logger
import datetime

import helper.llm_utils as llm_utils
import helper.utils as utils
import helper.database_functions as db_funcs
    
if __name__ == "__main__":
    db, cursor = db_funcs.initialize_database()
    if not all([st.session_state['start_date'], 
    st.session_state['end_date'],
    st.session_state['start_time'],
    st.session_state['end_time']]):
        st.warning(icon="🚨", body="Ensure Timelines are set, and times are scheduled in the Todolist Tab")
        st.stop()
    st.info("Click Generate plan, to view the structure of the plan.")
    st.info("Click Send to Calander, for the plan to be synced to calander.")
    if st.button("Generate plan"):
        prompt = f"Using the previous messages as context. Generate a detailed plan starting from date {st.session_state['start_date']} to {st.session_state['end_date']} scheduled each day from start_time {st.session_state['start_time']} to {st.session_state['end_time']}"
        with st.spinner('Generating Plan... please wait'):
            response_text = llm_utils.generate_plan_response(prompt, st.session_state['plan_model'], db, cursor)
            st.session_state['plan'] = llm_utils.parse_plan_response(response_text)
            # for day in st.session_state['plan']:
            #     logger.debug(day)
            #     start_datetime = datetime.datetime.strptime(f"{day['date']} {day['start_time']}", "%Y-%m-%d %H:%M:%S")
            #     end_datetime = datetime.datetime.strptime(f"{day['date']} {day['start_time']}", "%Y-%m-%d %H:%M:%S")
            #     st.write(f"""{start_datetime,
            #             end_datetime,
            #             day["goal"],
            #             day["task"],
            #             day["start_time"],
            #             day["end_time"]}
            #             """)
    with st.container(height=300):
        if st.session_state['plan']:
            st.json(st.session_state['plan'])

    if st.button("Send to Calander"):
        with st.spinner("Syncing plan to Calander..."):
            service = utils.get_calendar_service()
            if service:
                timezone = utils.get_user_timezone(service)
                # logger.debug(st.session_state['plan'])
                st.write(f"Your timezone is: {timezone}")
                
                for day in st.session_state['plan']:
                    start_datetime = datetime.datetime.strptime(f"{day['date']} {day['start_time']}", "%Y-%m-%d %H:%M:%S")
                    end_datetime = datetime.datetime.strptime(f"{day['date']} {day['start_time']}", "%Y-%m-%d %H:%M:%S")
                    calendar_event = utils.create_event(
                        service,
                        start_datetime,
                        end_datetime,
                        day["goal"],
                        day["task"],
                        timezone)
                    st.write(f"Event created: {calendar_event.get('htmlLink')}")