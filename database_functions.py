import sqlite3
import json

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

# Save user data
def save_user(cursor, sql_db, email: str, name: str, picture: str):
    cursor.execute('INSERT OR IGNORE INTO users (email, name, picture) VALUES (?, ?, ?)', (email, name, picture))
    sql_db.commit()

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