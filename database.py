import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from logger_config import setup_logger

# Load environment variables
load_dotenv()
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot.db')

# Setup logger
logger = setup_logger('database', 'database.log')

def log_db_operation(operation: str, details: str):
    """Log database operations with timestamp"""
    logger.info(f"DB {operation}: {details}")

def init_db():
    """Initialize the database with required tables."""
    try:
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
            log_db_operation("INIT", f"Database initialized at {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        yield conn
        conn.commit()  # Commit the transaction
        logger.debug("Database transaction committed successfully")
    except Exception as e:
        if conn:
            conn.rollback()  # Rollback on error
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# User level functions
def set_user_level(user_id: int, level: str):
    """Set or update user's English proficiency level."""
    try:
        with get_db() as db:
            db.execute('''
                INSERT OR REPLACE INTO user_levels (user_id, level)
                VALUES (?, ?)
            ''', (user_id, level))
            log_db_operation("UPDATE", f"User {user_id} level set to {level}")
    except Exception as e:
        logger.error(f"Error setting user level: {e}")
        raise

def get_user_level(user_id: int) -> str:
    """Get user's English proficiency level."""
    try:
        with get_db() as db:
            cursor = db.execute('''
                SELECT level FROM user_levels WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            level = result[0] if result else "beginner"
            log_db_operation("SELECT", f"Retrieved level for user {user_id}: {level}")
            return level
    except Exception as e:
        logger.error(f"Error getting user level: {e}")
        raise

# Conversation functions
def add_message(user_id: int, role: str, message: str):
    """Add a message to the conversation history."""
    try:
        with get_db() as db:
            db.execute('''
                INSERT INTO conversations (user_id, role, message)
                VALUES (?, ?, ?)
            ''', (user_id, role, message))
            log_db_operation("INSERT", f"New message from {role} for user {user_id}")
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise

def get_conversation(user_id: int, limit: int = 10) -> list:
    """Get recent conversation history for a user."""
    try:
        with get_db() as db:
            cursor = db.execute('''
                SELECT role, message FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            result = [(row[0], row[1]) for row in cursor.fetchall()][::-1]
            log_db_operation("SELECT", f"Retrieved {len(result)} messages for user {user_id}")
            return result
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise

def clear_conversation(user_id: int):
    """Clear conversation history for a user."""
    try:
        with get_db() as db:
            db.execute('''
                DELETE FROM conversations WHERE user_id = ?
            ''', (user_id,))
            log_db_operation("DELETE", f"Cleared conversation history for user {user_id}")
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise

# Initialize database when module is imported
try:
    init_db()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    raise 