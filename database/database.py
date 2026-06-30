import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def save_event(event_type, image_path):
    """
    Save a security event into the Sentinel AI database.
    """

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO events
        (
            event_type,
            timestamp,
            image_path
        )
        VALUES (?, ?, ?)
        """,
        (
            event_type,
            timestamp,
            image_path
        )
    )

    connection.commit()
    connection.close()