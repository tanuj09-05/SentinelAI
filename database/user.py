import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from config import DATABASE_PATH


def _connect():
    """
    Open a SQLite connection with WAL mode and a 10-second busy timeout.
    WAL allows concurrent reads while a write is in progress, eliminating
    the 'database is locked' errors that occur during signup (which inserts
    into both 'users' and 'user_settings' in close succession).
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def create_user(name, email, password):
    """
    Create a new user with name, email, and password.
    Returns True if successful, False if email already exists.
    """
    try:
        with _connect() as connection:
            cursor = connection.cursor()

            password_hash = generate_password_hash(password)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password_hash, created_at),
            )

            user_id = cursor.lastrowid

            # Create default settings for the new user in the same transaction
            # to avoid a second connection while the first is still open.
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO user_settings
                (user_id, camera_source, camera_index, smtp_port, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, "index", 0, 587, updated_at, updated_at),
            )

            connection.commit()

        return True

    except sqlite3.IntegrityError:
        # Email already exists
        return False


def get_user_by_email(email):
    """
    Fetch user by email address.
    Returns user tuple (id, name, email, password_hash, created_at) or None.
    """
    with _connect() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
            (email,),
        )

        return cursor.fetchone()


def get_user_by_id(user_id):
    """
    Fetch user by ID.
    Returns user tuple (id, name, email, password_hash, created_at) or None.
    """
    with _connect() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        )

        return cursor.fetchone()


def verify_password(password_hash, password):
    """
    Verify if the provided password matches the hash.
    """
    return check_password_hash(password_hash, password)


def get_user_settings(user_id):
    """
    Fetch user settings by user_id.
    Returns settings tuple or None.
    """
    with _connect() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, user_id, smtp_host, smtp_port, smtp_username, smtp_password,
                   sender_email, receiver_email, camera_source, camera_index, rtsp_url,
                   created_at, updated_at
            FROM user_settings WHERE user_id = ?
            """,
            (user_id,),
        )

        return cursor.fetchone()


def ensure_user_settings(user_id):
    """
    Ensure a settings row exists for the user.
    Creates default settings when missing.
    Uses a single connection for both the check and the insert to avoid
    opening a nested connection that would cause a database lock.
    """
    with _connect() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, user_id, smtp_host, smtp_port, smtp_username, smtp_password,
                   sender_email, receiver_email, camera_source, camera_index, rtsp_url,
                   created_at, updated_at
            FROM user_settings WHERE user_id = ?
            """,
            (user_id,),
        )
        existing = cursor.fetchone()

        if existing:
            return existing

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO user_settings
            (user_id, camera_source, camera_index, smtp_port, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "index", 0, 587, timestamp, timestamp),
        )

        connection.commit()

        cursor.execute(
            """
            SELECT id, user_id, smtp_host, smtp_port, smtp_username, smtp_password,
                   sender_email, receiver_email, camera_source, camera_index, rtsp_url,
                   created_at, updated_at
            FROM user_settings WHERE user_id = ?
            """,
            (user_id,),
        )
        return cursor.fetchone()


def save_user_settings(
    user_id,
    smtp_host,
    smtp_port,
    smtp_username,
    smtp_password,
    sender_email,
    receiver_email,
    camera_source,
    camera_index,
    rtsp_url,
):
    """
    Save or update user settings.
    """
    ensure_user_settings(user_id)

    with _connect() as connection:
        cursor = connection.cursor()

        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE user_settings
            SET smtp_host = ?, smtp_port = ?, smtp_username = ?, smtp_password = ?,
                sender_email = ?, receiver_email = ?, camera_source = ?,
                camera_index = ?, rtsp_url = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (
                smtp_host,
                smtp_port,
                smtp_username,
                smtp_password,
                sender_email,
                receiver_email,
                camera_source,
                camera_index,
                rtsp_url,
                updated_at,
                user_id,
            ),
        )

        connection.commit()

    return True
