import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot.db')  # Use 'bot.db' as default if not set

def init_db():
    """Initialize the database with required tables."""
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id INTEGER PRIMARY KEY,
                level TEXT NOT NULL
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_levels(user_id)
            )
        ''')

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

# User level functions
def set_user_level(user_id: int, level: str):
    """Set or update user's English proficiency level."""
    with get_db() as db:
        db.execute('''
            INSERT OR REPLACE INTO user_levels (user_id, level)
            VALUES (?, ?)
        ''', (user_id, level))

def get_user_level(user_id: int) -> str:
    """Get user's English proficiency level."""
    with get_db() as db:
        cursor = db.execute('''
            SELECT level FROM user_levels WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else "beginner"  # Default to beginner if not set

# Conversation functions
def add_message(user_id: int, role: str, message: str):
    """Add a message to the conversation history."""
    with get_db() as db:
        db.execute('''
            INSERT INTO conversations (user_id, role, message)
            VALUES (?, ?, ?)
        ''', (user_id, role, message))

def get_conversation(user_id: int, limit: int = 10) -> list:
    """Get recent conversation history for a user."""
    with get_db() as db:
        cursor = db.execute('''
            SELECT role, message FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        return [(row[0], row[1]) for row in cursor.fetchall()][::-1]  # Reverse to get chronological order

def clear_conversation(user_id: int):
    """Clear conversation history for a user."""
    with get_db() as db:
        db.execute('''
            DELETE FROM conversations WHERE user_id = ?
        ''', (user_id,))

# Initialize database when module is imported
init_db() 