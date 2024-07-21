import streamlit as st
import psycopg2
import json
from cryptography.fernet import Fernet
from logzero import logger
import base64
import binascii
import cryptography

def load_key():
    fernet_key_str = st.secrets["encryption_key"]
    return Fernet(fernet_key_str.encode())

cipher = load_key()

def initialize_database():
    database_url = st.secrets["database_url"]
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        picture TEXT,
        gemini_api_key TEXT
    )
    ''')
    
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

def is_user_present(cursor, email: str) -> bool:
    cursor.execute('SELECT email FROM users WHERE email=%s', (email,))
    return cursor.fetchone() is not None

def save_user(cursor, connection, email: str, name: str, picture: str, gemini_api_key: str = None):
    if gemini_api_key:
        encrypted_key = cipher.encrypt(gemini_api_key.encode())
        encrypted_key_base64 = base64.urlsafe_b64encode(encrypted_key).decode('utf-8')
        cursor.execute('INSERT INTO users (email, name, picture, gemini_api_key) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture, gemini_api_key = EXCLUDED.gemini_api_key', (email, name, picture, encrypted_key_base64))
    else:
        cursor.execute('INSERT INTO users (email, name, picture) VALUES (%s, %s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture', (email, name, picture))
    connection.commit()

def get_user_api_key(cursor, email: str):
    cursor.execute('SELECT gemini_api_key FROM users WHERE email=%s', (email,))
    result = cursor.fetchone()
    if result and result[0]:
        try:
            encrypted_key_base64 = result[0].encode('utf-8')
            encrypted_key = base64.urlsafe_b64decode(encrypted_key_base64)
            decrypted_key = cipher.decrypt(encrypted_key).decode('utf-8')
            logger.debug(f"Fetched decrypted API key {decrypted_key} for {email}")
            return decrypted_key
        except (binascii.Error, ValueError, cryptography.fernet.InvalidToken) as e:
            logger.error(f"Error decrypting API key for {email}: {e}")
            return None
    logger.debug(f"No API key found for {email}")
    return None

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
    # cursor.execute('INSERT INTO summaries (email, summary, timestamp) VALUES (%s, %s, %s)', (email, summary))
    conn.commit()

def get_latest_summary(cursor, email: str):
    """
    Returns the latest summary along with the timestamp if present, else returns None, None.
    """
    cursor.execute('SELECT summary, timestamp FROM summaries WHERE email=%s', (email,))
    result = cursor.fetchone()
    if result:
        return result[0], result[1] 
    return None, None