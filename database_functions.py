import sqlite3
import json
from cryptography.fernet import Fernet
import config
from logzero import logger

def load_key():
    return Fernet(config.encryption_key)

cipher = load_key()

def initialize_database():
    # Initialize SQLite database
    sql_db = sqlite3.connect('user_data.db')
    c = sql_db.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT,
        picture TEXT
    )
    ''')

    add_gemini_api_key_column(c, sql_db)

    c.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        task_text TEXT,
        subtasks TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        role TEXT,
        parts TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    return sql_db, c


def add_gemini_api_key_column(cursor, sql_db):
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'gemini_api_key' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN gemini_api_key TEXT")
        sql_db.commit()


# Save user data
def save_user(cursor, sql_db, email: str, name: str, picture: str, gemini_api_key: str = None):
    if gemini_api_key:
        encrypted_key = cipher.encrypt(gemini_api_key.encode())
        cursor.execute('INSERT OR REPLACE INTO users (email, name, picture, gemini_api_key) VALUES (?, ?, ?, ?)', (email, name, picture, encrypted_key))
    else:
        cursor.execute('INSERT OR IGNORE INTO users (email, name, picture) VALUES (?, ?, ?)', (email, name, picture))
    sql_db.commit()

#Get user api key
def get_user_api_key(cursor, email: str):
    cursor.execute('SELECT gemini_api_key FROM users WHERE email=?', (email,))
    result = cursor.fetchone()
    if result and result[0]:
        decrypted_key = cipher.decrypt(result[0]).decode()
        logger.debug(f"Fetched decrypted API key {decrypted_key} for {email}")
        return decrypted_key
    logger.debug(f"No API key found for {email}")
    return None

# Save chat message
def save_chat_message(cursor, sql_db, user_id: int, role: str, content: str):
    parts = json.dumps([content])
    cursor.execute('INSERT INTO chat_messages (user_id, role, parts) VALUES (?, ?, ?)', (user_id, role, parts))
    sql_db.commit()

# Fetch user ID
def get_user_id(cursor, email: str):
    cursor.execute('SELECT id FROM users WHERE email=?', (email,))
    result = cursor.fetchone()
    return result[0] if result else None

# Fetch user chat messages
def get_user_chat_messages(cursor, user_id: int):
    cursor.execute('SELECT role, parts FROM chat_messages WHERE user_id=? ORDER BY id ASC', (user_id,))
    messages = cursor.fetchall()
    result = []
    for role, parts in messages:
        try:
            parts = json.loads(parts)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for message with role {role} and parts {parts}")
            parts = [parts]
        result.append({"role": role, "parts": parts})
    return result

def view_first_few_rows():
    # Connect to SQLite database
    sql_db = sqlite3.connect('user_data.db')
    c = sql_db.cursor()

    # Fetch the first few rows of the chat_messages table
    c.execute('SELECT * FROM chat_messages LIMIT 5')
    rows = c.fetchall()

    # Print the rows
    for row in rows:
        print(row)

    # Close the database connection
    sql_db.close()

def update_roles_in_database(cursor, sql_db):
    # Update existing roles from 'assistant' to 'model'
    cursor.execute("UPDATE chat_messages SET role = 'model' WHERE role = 'assistant'")
    sql_db.commit()