import sqlite3
import json
import time
from pathlib import Path
from contextlib import contextmanager
from agent.configs.config import agent_settings

# Database file placed in data/ directory
DATA_DIR = agent_settings.BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "agent.db"

def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    #PRAGMA optimizations for concurrent agent turns
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    """Context manager for safe database transactions with auto-commit and rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize schema and runs legacy JSON auto-migration if needed."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXIST sessions(
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Session',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                is_archived INTEGER NOT NULL DEFAULT 0,
                metadata JSONB NOT NULL DEFAULT '{}'
            );
            """
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_id TEXT,
                role TEXT NOT NULL, 
                sender TEXT NOT NULL DEFAULT 'supervisor',
                content TEXT NOT NULL,
                files TEXT,
                metadata JSONB NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_time 
            ON messages(session_id, created_at);
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subagent_tasks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_id TEXT,
                task_index INTEGER NOT NULL,
                task_description TEXT NOT NULL,
                status TEXT NOT NULL,
                code TEXT,
                stdout TEXT,
                stderr TEXT,
                files TEXT,
                attempts INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_session
            ON subagent_tasks(session_id, created_at);
        """)
