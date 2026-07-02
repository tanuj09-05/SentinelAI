import sqlite3

# We connect to the SQLite database file stored inside the database folder.
# If the file does not exist yet, SQLite creates it automatically.
database_path = "database/sentinelai.db"
connection = sqlite3.connect(database_path)

# A cursor lets us send SQL commands to the database.
cursor = connection.cursor()

# Drop existing tables to ensure clean schema
cursor.execute("DROP TABLE IF EXISTS events")
cursor.execute("DROP TABLE IF EXISTS user_settings")
cursor.execute("DROP TABLE IF EXISTS users")

# Create users table
create_users_table_query = """
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

cursor.execute(create_users_table_query)

# Create user_settings table for storing user-specific SMTP and camera settings
create_settings_table_query = """
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
"""

cursor.execute(create_settings_table_query)

# Create events table to store detection events
create_events_table_query = """
CREATE TABLE events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type TEXT,
    timestamp TEXT,
    image_path TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
"""

cursor.execute(create_events_table_query)

# commit() saves the changes permanently in the database file.
connection.commit()

# close() safely ends the connection after the tables are created.
connection.close()

print("Database Created")
