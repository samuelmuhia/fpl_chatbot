import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv('DATABASE_PATH', 'fpl_assistant.db')


def get_db_path():
    return DB_PATH


def initialize_database(token: str):
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
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            username TEXT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cursor.execute('PRAGMA table_info(chat_history)')
    columns = [row[1] for row in cursor.fetchall()]
    if 'session_id' not in columns:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN session_id INTEGER')

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        '''
    )

    if token:
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


def create_chat_session(username: str, name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_sessions (username, name, created_at) VALUES (?, ?, ?)',
        (username, name, datetime.utcnow().isoformat())
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def list_chat_sessions(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, created_at FROM chat_sessions WHERE username = ? ORDER BY created_at DESC',
        (username,)
    )
    sessions = [dict(id=row[0], name=row[1], created_at=row[2]) for row in cursor.fetchall()]
    conn.close()
    return sessions


def get_chat_session(session_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, name, created_at FROM chat_sessions WHERE id = ?',
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(id=row[0], username=row[1], name=row[2], created_at=row[3]) if row else None


def get_chat_history(session_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT username, role, message, created_at FROM chat_history WHERE session_id = ? ORDER BY id ASC',
        (session_id,)
    )
    history = [
        dict(username=row[0], role=row[1], message=row[2], created_at=row[3])
        for row in cursor.fetchall()
    ]
    conn.close()
    return history


def save_chat(session_id: int, username: str, role: str, message: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_history (session_id, username, role, message, created_at) VALUES (?, ?, ?, ?, ?)',
        (session_id, username, role, message, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
