import sqlite3
from datetime import datetime
from config import DATABASE_PATH

def ensure_database_schema():
    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                smtp_host TEXT,
                smtp_port INTEGER DEFAULT 587,
                smtp_username TEXT,
                smtp_password TEXT,
                sender_email TEXT,
                receiver_email TEXT,
                camera_source TEXT DEFAULT 'index',
                camera_index INTEGER DEFAULT 0,
                rtsp_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT,
                timestamp TEXT,
                image_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("DELETE FROM user_settings WHERE user_id NOT IN (SELECT id FROM users)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faces(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                photo_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        try:
            cursor.execute("ALTER TABLE events ADD COLUMN track_id INTEGER")
            cursor.execute("ALTER TABLE events ADD COLUMN entry_time TEXT")
            cursor.execute("ALTER TABLE events ADD COLUMN exit_time TEXT")
            cursor.execute("ALTER TABLE events ADD COLUMN duration REAL")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE events ADD COLUMN recognized_name TEXT")
            cursor.execute("ALTER TABLE events ADD COLUMN is_known BOOLEAN")
        except sqlite3.OperationalError:
            pass

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")

        connection.commit()

def save_event(
    user_id,
    event_type,
    image_path,
    track_id=None,
    entry_time=None,
    exit_time=None,
    duration=None,
    recognized_name=None,
    is_known=None,
):
    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO events (
                user_id, event_type, timestamp, image_path, track_id, 
                entry_time, exit_time, duration, recognized_name, is_known
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, event_type, timestamp, image_path, track_id,
                entry_time, exit_time, duration, recognized_name, is_known
            )
        )
        connection.commit()
