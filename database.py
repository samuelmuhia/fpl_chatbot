import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv('DATABASE_PATH', 'fpl_assistant.db')


def get_db_path():
    return DB_PATH


def initialize_database(token: str):
    if not token:
        raise RuntimeError('Database initialization requires a valid token.')

    db_path = get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        '''
    )

    cursor.execute(
        'INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
        ('db_token', token[:64])
    )

    conn.commit()
    return conn


def get_db_connection():
    return sqlite3.connect(get_db_path(), check_same_thread=False)


def find_user(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def create_user(username: str, password_hash: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
            (username, password_hash, datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def save_chat(username: str, role: str, message: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_history (username, role, message, created_at) VALUES (?, ?, ?, ?)',
        (username, role, message, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
