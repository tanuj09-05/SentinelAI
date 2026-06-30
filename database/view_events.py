import sqlite3

# We open the same SQLite database file that stores all event records.
# If the file already exists, SQLite connects to it.
database_path = "database/sentinelai.db"
connection = sqlite3.connect(database_path)

# A cursor is used to send SQL commands to the database.
cursor = connection.cursor()

# This query reads every row from the events table.
select_all_events_query = "SELECT * FROM events"
cursor.execute(select_all_events_query)

# fetchall() returns all rows from the query as a list of tuples.
rows = cursor.fetchall()

# Print each row one by one so we can see the stored event data.
for row in rows:
    print(row)

# Always close the connection after we finish using the database.
connection.close()