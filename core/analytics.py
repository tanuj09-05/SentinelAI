import sqlite3
from config import DATABASE_PATH

def get_dashboard_stats():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = DATE('now')")
        today = cursor.fetchone()[0]

    return {"total_alerts": total, "today_alerts": today}
