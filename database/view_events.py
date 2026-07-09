import sqlite3

connection = sqlite3.connect("database/sentinelai.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM events")

for row in cursor.fetchall():
    print(row)

connection.close()
