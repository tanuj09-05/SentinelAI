import sqlite3

from config import DATABASE_PATH


def get_dashboard_stats():
    """
    Connects to the SQLite database and retrieves basic statistics for the dashboard.

    This function counts the total number of security events (alerts) ever recorded,
    as well as the number of events that occurred today.

    Returns:
        dict: A dictionary containing 'total_alerts' and 'today_alerts' as integers.
    """

    # Open a connection to the SQLite database using a context manager (the 'with' statement).
    # This ensures the connection is automatically closed when we are done, preventing memory leaks.
    with sqlite3.connect(DATABASE_PATH) as database_connection:

        # Create a cursor object which allows us to execute SQL commands
        database_cursor = database_connection.cursor()

        # --- 1. Get the Total Alerts ---
        # Execute a SQL query to count every single row in the 'events' table
        database_cursor.execute("SELECT COUNT(*) FROM events")

        # fetchone() returns a tuple (e.g., (50,)), so we get the first item [0] to extract the integer 50.
        total_alerts_count = database_cursor.fetchone()[0]

        # --- 2. Get Today's Alerts ---
        # Execute a SQL query to count rows where the 'timestamp' column matches today's date
        database_cursor.execute("""
            SELECT COUNT(*)
            FROM events
            WHERE DATE(timestamp) = DATE('now')
        """)

        # Extract the integer from the result tuple
        today_alerts_count = database_cursor.fetchone()[0]

    # Return the collected statistics as a dictionary so the frontend can easily read them
    return {"total_alerts": total_alerts_count, "today_alerts": today_alerts_count}
