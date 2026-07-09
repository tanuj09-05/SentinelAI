import sqlite3

connection = sqlite3.connect("database/sentinelai.db")
cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS events")
cursor.execute("DROP TABLE IF EXISTS user_settings")
cursor.execute("DROP TABLE IF EXISTS users")

cursor.execute("""
    CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE user_settings(
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
    CREATE TABLE events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_type TEXT,
        timestamp TEXT,
        image_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")

connection.commit()
connection.close()

print("Database Created")
