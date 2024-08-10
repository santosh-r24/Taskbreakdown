import streamlit as st
import psycopg2
import json
from logzero import logger
import datetime

def initialize_database():
    database_url = st.secrets["database_url"]
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        picture TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goal_plan (
        email TEXT PRIMARY KEY,
        plan JSONB,
        task_ids JSONB,
        FOREIGN KEY(email) REFERENCES users(email)
    )
    ''')

    # Create a new table goal_plan that stores plan, tasks_id (from google tasks), and dates foregin key being email, and references user
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        email TEXT,
        role TEXT,
        parts TEXT,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(email) REFERENCES users(email)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS summaries (
        id SERIAL PRIMARY KEY,
        email TEXT,
        summary TEXT,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(email) REFERENCES users(email)
    )
    ''')

    connection.commit()
    return connection, cursor

def check_if_google_tasks_are_created(cursor, email:str) -> bool:
    cursor.execute('SELECT task_ids FROM goal_plan WHERE email=%s', (email,))
    result = cursor.fetchone()
    return result is not None and result[0] is not None

def fetch_plan_if_generated(cursor, email:str):
    cursor.execute('SELECT plan FROM goal_plan WHERE email=%s', (email,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def save_plan(cursor, connection, email: str, plan: json):
    cursor.execute('INSERT INTO goal_plan (email, plan) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET plan = EXCLUDED.plan', (email, json.dumps(plan)))
    connection.commit()

def fetch_task_ids(cursor, email: str):
    cursor.execute('SELECT task_ids FROM goal_plan WHERE email=%s', (email,))
    result = cursor.fetchone()
    if result and result[0]:
        return json.loads(result[0])
    return {}

def save_task_ids(cursor, connection, email: str, task_id: str, date: datetime):
    logger.debug("Tasks are being saved ")
    task_date = date.strftime('%Y-%m-%d')
    task_id_entry = {task_date: task_id}
    cursor.execute('''
        UPDATE goal_plan
        SET task_ids = '{}'
        WHERE email = %s AND task_ids IS NULL
    ''', (email,))
    cursor.execute(
        'INSERT INTO goal_plan (email, task_ids) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET task_ids = goal_plan.task_ids || %s::jsonb',
        (email, json.dumps(task_id_entry), json.dumps(task_id_entry))
    )
    connection.commit()

def is_user_present(cursor, email: str) -> bool:
    cursor.execute('SELECT email FROM users WHERE email=%s', (email,))
    return cursor.fetchone() is not None

def save_user(cursor, connection, email: str, name: str, picture: str):
    cursor.execute('INSERT INTO users (email, name, picture) VALUES (%s, %s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture', (email, name, picture))
    connection.commit()

def get_message_count_within_timeframe(cursor, email, timeframe):
    """
    cursor: cursor
    email: email of user
    timeframe: duration till which rate_limit will apply to cap messages. This is set to 1 hour by default.
    
    returns
    message_count: integer value of how many messages have been sent by user in the past 1 hour.
    """
    current_time = datetime.datetime.now(datetime.timezone.utc)
    timeframe_start = current_time - timeframe
    cursor.execute(
        "SELECT COUNT(*) FROM chat_messages WHERE email = %s AND timestamp >= %s AND role = 'user'",
        (email, timeframe_start)
    )
    message_count = cursor.fetchone()[0]
    return message_count

def save_chat_message(cursor, connection, email: str, role: str, content: str):
    parts = json.dumps([content])
    cursor.execute('INSERT INTO chat_messages (email, role, parts) VALUES (%s, %s, %s)', (email, role, parts))
    connection.commit()

def get_user_chat_messages(cursor, email: str, timestamp=None):
    """
    Fetches chat messages after timestamp if timestamp is passed. Else, fetches all messages.
    """
    if timestamp:
        cursor.execute('SELECT role, parts FROM chat_messages WHERE email=%s AND timestamp > %s ORDER BY id ASC', (email, timestamp))
    else:
        cursor.execute('SELECT role, parts FROM chat_messages WHERE email=%s ORDER BY id ASC', (email,))
    messages = cursor.fetchall()
    result = []
    for role, parts in messages:
        try:
            parts = json.loads(parts)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON for message with role {role} and parts {parts}")
            parts = [parts]
        result.append({"role": role, "parts": parts})
    return result

def save_summary(cursor, conn, email: str, summary: str, timestamp):
    cursor.execute('INSERT INTO summaries (email, summary, timestamp) VALUES (%s, %s, %s) ON CONFLICT (email) DO UPDATE SET summary = EXCLUDED.summary, timestamp = EXCLUDED.timestamp', (email, summary, timestamp))
    conn.commit()

def get_latest_summary(cursor, email: str):
    """
    Returns the latest summary along with the timestamp if present, else returns None, None.
    """
    cursor.execute('SELECT summary, timestamp FROM summaries WHERE email=%s', (email,))
    result = cursor.fetchone()
    if result:
        logger.debug(f"get_latest_summary found: {result}")
        return result[0], result[1] 
    logger.debug(f"No summary found")
    return None, None

def delete_chat(cursor, connection, email:str):
    """
    Delete chats for a particular user. Returns True if succeeded.
    """
    try:
        cursor.execute('DELETE FROM chat_messages WHERE email = %s', (email,))
        connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error clearing chat messages for {email}: {e}")
        connection.rollback()
        return False
    
def delete_summaries(cursor, connection, email:str):
    """
    Delete summaries for a particular user. Returns True, if suceeded.
    """
    try:
        cursor.execute('DELETE FROM summaries WHERE email = %s', (email,))
        connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error clearing summaries for {email}: {e}")
        connection.rollback()
        return False