import sqlite3


# We connect to the SQLite database file stored inside the database folder.
# If the file does not exist yet, SQLite creates it automatically.
database_path = "database/sentinelai.db"
connection = sqlite3.connect(database_path)

# A cursor lets us send SQL commands to the database.
cursor = connection.cursor()

# This SQL command creates the events table only if it does not already exist.
# The table stores information about each detected event.
create_events_table_query = """
CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    timestamp TEXT,
    image_path TEXT
)
"""

cursor.execute(create_events_table_query)

# commit() saves the changes permanently in the database file.
connection.commit()

# close() safely ends the connection after the table is created.
connection.close()

print("Database Created")