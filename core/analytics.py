import sqlite3
from config import DATABASE_PATH


def get_dashboard_stats():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Total alerts
    cursor.execute("SELECT COUNT(*) FROM events")
    total_alerts = cursor.fetchone()[0]

    # Today's alerts
    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE DATE(timestamp)=DATE('now')
    """)
    today_alerts = cursor.fetchone()[0]

    connection.close()

    return {
        "total_alerts": total_alerts,
        "today_alerts": today_alerts
    }