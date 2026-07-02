import os
import sqlite3
import time
import psutil


import cv2
import numpy as np
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, redirect, url_for
from flask_login import LoginManager, login_required, current_user

from config import DATABASE_PATH
from core.camera_manager import CameraManager
from core.detector import get_ai_status
from database.database import ensure_database_schema
from database.user import get_user_by_id, get_user_settings

from routes.faces import faces_bp
from routes.auth import auth_bp, User
from routes.report import report_bp
from routes.settings import settings_bp

load_dotenv()

ensure_database_schema()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID for Flask-Login.
    """
    try:
        user_data = get_user_by_id(int(user_id))
        if user_data:
            user_id, name, email, password_hash, created_at = user_data
            return User(user_id, name, email)
    except (ValueError, TypeError):
        pass
    return None


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(report_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(faces_bp)


def _get_black_frame_jpeg(text="Camera Offline"):
    """Return a cached JPEG of a black 640x480 frame."""
    black = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(black, text, (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (80, 80, 80), 2)
    _, buf = cv2.imencode(".jpg", black)
    return buf.tobytes()


def generate_frames(user_id=None):
    """
    Generator that fetches the latest processed frame from the user's
    background camera thread. Does not block the web server.
    """
    if not user_id:
        # If accessed without login, yield an error frame
        placeholder = _get_black_frame_jpeg("Not Authenticated")
        while True:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + placeholder + b"\r\n"
            )
            time.sleep(1)

    thread = CameraManager.get_thread(user_id)

    while True:
        frame = thread.get_jpeg()
        if frame:
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        # Sleep slightly to prevent high CPU usage in the generator loop
        time.sleep(0.05)


@app.route("/")
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        # Select explicit columns so that template indices are stable even if
        # the schema gains new columns in future. Column order returned:
        # 0=id, 1=event_type, 2=timestamp, 3=image_path
        cursor.execute(
            """
            SELECT id, event_type, timestamp, image_path
            FROM events
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (current_user.id,),
        )
        events = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) FROM events WHERE user_id = ?", (current_user.id,)
        )
        total_events = cursor.fetchone()[0]

    latest_event = events[0] if events else None

    return render_template(
        "dashboard.html",
        events=events,
        total_events=total_events,
        latest_event=latest_event,
    )


@app.route("/video_feed")
def video_feed():
    # NOTE: @login_required is intentionally NOT used here.
    # The dashboard page is already @login_required, so only authenticated
    # users will ever have this URL loaded. Applying @login_required to the
    # MJPEG stream endpoint causes the browser's <img> sub-request to receive
    # an HTML redirect to /auth/login instead of JPEG frames, producing a
    # blank/broken camera feed.
    user_id = current_user.id if current_user.is_authenticated else None
    return Response(
        generate_frames(user_id), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/status")
@login_required
def api_status():
    status = CameraManager.get_thread(current_user.id).get_status()
    return jsonify(status)


@app.route("/api/system_metrics")
@login_required
def api_system_metrics():
    # CPU & RAM
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent

    status = CameraManager.get_thread(current_user.id).get_status()
    latency = status.get("latency", 0)
    fps = status.get("fps", 0)
    camera_status = status.get("camera", "offline").lower()

    # Database Status
    try:
        with sqlite3.connect(DATABASE_PATH, timeout=5) as connection:
            connection.execute("SELECT 1").fetchone()
            db_status = "online"
    except:
        db_status = "offline"

    # AI Engine Status
    ai_status = get_ai_status()

    # Email Service
    user_settings = get_user_settings(current_user.id)
    if (
        user_settings and user_settings[2] and user_settings[5]
    ):  # smtp_host and smtp_password
        email_status = "online"
    else:
        email_status = "not configured"

    # Analytics Engine
    analytics_status = "online" if db_status == "online" else "offline"

    return jsonify(
        {
            "cpu": cpu_usage,
            "ram": ram_usage,
            "latency": latency,
            "fps": fps,
            "services": {
                "ai": ai_status,
                "camera": camera_status,
                "database": db_status,
                "auth": "online" if current_user.is_authenticated else "offline",
                "email": email_status,
                "analytics": analytics_status,
            },
        }
    )


@app.route("/api/alerts")
@login_required
def api_alerts():

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, event_type, timestamp
            FROM events
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """,
            (current_user.id,),
        )

        alerts = cursor.fetchall()

    return jsonify([{"id": row[0], "event": row[1], "time": row[2]} for row in alerts])


@app.route("/api/analytics")
@login_required
def api_analytics():

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT DATE(timestamp), COUNT(*)
            FROM events
            WHERE user_id = ?
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        """,
            (current_user.id,),
        )

        rows = cursor.fetchall()

    labels = []
    values = []

    for row in rows:

        labels.append(row[0])
        values.append(row[1])

    return jsonify({"labels": labels, "values": values})


@app.route("/api/search")
@login_required
def api_search():

    keyword = request.args.get("q", "")

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, event_type, timestamp, image_path
            FROM events
            WHERE user_id = ?
              AND (event_type LIKE ?
                   OR timestamp LIKE ?)
            ORDER BY id DESC
        """,
            (current_user.id, f"%{keyword}%", f"%{keyword}%"),
        )

        rows = cursor.fetchall()

    return jsonify(rows)


@app.route("/analytics")
@login_required
def analytics():
    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT DATE(timestamp), COUNT(*)
            FROM events
            WHERE user_id = ?
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
            """,
            (current_user.id,),
        )
        daily_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT DATE(timestamp), COUNT(*)
            FROM events
            WHERE user_id = ?
              AND DATE(timestamp) >= DATE('now', '-6 day')
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
            """,
            (current_user.id,),
        )
        weekly_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT strftime('%Y-%m', timestamp), COUNT(*)
            FROM events
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', timestamp)
            ORDER BY strftime('%Y-%m', timestamp)
            """,
            (current_user.id,),
        )
        monthly_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT event_type, COUNT(*)
            FROM events
            WHERE user_id = ?
            GROUP BY event_type
            ORDER BY COUNT(*) DESC
            """,
            (current_user.id,),
        )
        event_type_rows = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) FROM events WHERE user_id = ?", (current_user.id,)
        )
        total_events = cursor.fetchone()[0]

        try:
            cursor.execute(
                "SELECT COUNT(DISTINCT track_id) FROM events WHERE user_id = ? AND track_id IS NOT NULL",
                (current_user.id,),
            )
            unique_visitors = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT AVG(duration) FROM events WHERE user_id = ? AND event_type = 'Zone Exit'",
                (current_user.id,),
            )
            avg_dwell_res = cursor.fetchone()[0]
            avg_dwell = round(avg_dwell_res, 1) if avg_dwell_res else 0

            cursor.execute(
                "SELECT COUNT(*) FROM events WHERE user_id = ? AND event_type = 'Loitering'",
                (current_user.id,),
            )
            loitering_events = cursor.fetchone()[0] or 0

            # Face metrics
            cursor.execute(
                "SELECT COUNT(DISTINCT track_id) FROM events WHERE is_known = 1 AND user_id = ?",
                (current_user.id,),
            )
            known_visitors = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(DISTINCT track_id) FROM events WHERE is_known = 0 AND user_id = ?",
                (current_user.id,),
            )
            unknown_visitors = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT recognized_name FROM events WHERE is_known = 1 AND user_id = ? GROUP BY recognized_name ORDER BY COUNT(*) DESC LIMIT 1",
                (current_user.id,),
            )
            most_frequent_visitor = cursor.fetchone()
            most_frequent_visitor = (
                most_frequent_visitor[0] if most_frequent_visitor else "N/A"
            )

            recognition_accuracy = 0
            total_faces = known_visitors + unknown_visitors
            if total_faces > 0:
                recognition_accuracy = round((known_visitors / total_faces) * 100, 1)

        except sqlite3.OperationalError:
            # Fallback if tracking/face columns don't exist yet
            unique_visitors = 0
            avg_dwell = 0
            loitering_events = 0
            known_visitors = 0
            unknown_visitors = 0
            most_frequent_visitor = "N/A"
            recognition_accuracy = 0

    status = CameraManager.get_thread(current_user.id).get_status()

    return render_template(
        "analytics.html",
        total_events=total_events,
        unique_visitors=unique_visitors,
        avg_dwell=avg_dwell,
        loitering_events=loitering_events,
        known_visitors=known_visitors,
        unknown_visitors=unknown_visitors,
        most_frequent_visitor=most_frequent_visitor,
        recognition_accuracy=f"{recognition_accuracy}%",
        people_detected=status["people"],
        threat_level=status["threat"],
        camera_status=status["camera"],
        max_simultaneous=status.get("max_people", 0),
        daily_labels=[row[0] for row in daily_rows],
        daily_values=[row[1] for row in daily_rows],
        weekly_labels=[row[0] for row in weekly_rows],
        weekly_values=[row[1] for row in weekly_rows],
        monthly_labels=[row[0] for row in monthly_rows],
        monthly_values=[row[1] for row in monthly_rows],
        event_type_labels=[row[0] for row in event_type_rows],
        event_type_values=[row[1] for row in event_type_rows],
    )


@app.route("/alerts")
@login_required
def alerts():
    keyword = request.args.get("q", "").strip()
    selected_event_type = request.args.get("event_type", "All")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    if page < 1:
        page = 1

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT DISTINCT event_type FROM events WHERE user_id = ? ORDER BY event_type ASC",
            (current_user.id,),
        )
        event_types = [row[0] for row in cursor.fetchall()]

        conditions = ["user_id = ?"]
        parameters = [current_user.id]

        if keyword:
            conditions.append("(event_type LIKE ? OR timestamp LIKE ?)")
            parameters.extend([f"%{keyword}%", f"%{keyword}%"])

        if selected_event_type != "All":
            conditions.append("event_type = ?")
            parameters.append(selected_event_type)

        where_clause = " WHERE " + " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) FROM events{where_clause}"
        cursor.execute(count_query, parameters)
        total_alerts = cursor.fetchone()[0]

        total_pages = max((total_alerts + per_page - 1) // per_page, 1)

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * per_page

        alerts_query = f"""
            SELECT id, event_type, timestamp, image_path
            FROM events
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(alerts_query, parameters + [per_page, offset])
        alerts_rows = cursor.fetchall()

    return render_template(
        "alerts.html",
        alerts=alerts_rows,
        event_types=event_types,
        keyword=keyword,
        selected_event_type=selected_event_type,
        page=page,
        total_pages=total_pages,
        total_alerts=total_alerts,
    )


@app.route("/evidence")
@login_required
def evidence():
    keyword = request.args.get("q", "").strip()
    selected_event_type = request.args.get("event_type", "All")
    sort_by = request.args.get("sort", "id")
    sort_order = request.args.get("order", "desc").lower()

    allowed_sort_columns = {
        "id": "id",
        "timestamp": "timestamp",
        "event_type": "event_type",
    }

    selected_sort_column = allowed_sort_columns.get(sort_by, "id")
    selected_sort_order = "ASC" if sort_order == "asc" else "DESC"

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT DISTINCT event_type FROM events WHERE user_id = ? ORDER BY event_type ASC",
            (current_user.id,),
        )
        event_types = [row[0] for row in cursor.fetchall()]

        query = (
            "SELECT id, event_type, timestamp, image_path FROM events WHERE user_id = ?"
        )
        conditions = []
        parameters = [current_user.id]

        if keyword:
            conditions.append("(event_type LIKE ? OR timestamp LIKE ?)")
            parameters.extend([f"%{keyword}%", f"%{keyword}%"])

        if selected_event_type != "All":
            conditions.append("event_type = ?")
            parameters.append(selected_event_type)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += f" ORDER BY {selected_sort_column} {selected_sort_order}"

        cursor.execute(query, parameters)
        events = cursor.fetchall()

    return render_template(
        "evidence.html",
        events=events,
        event_types=event_types,
        keyword=keyword,
        selected_event_type=selected_event_type,
        selected_sort=sort_by,
        selected_order=sort_order,
    )


@app.route("/live")
@login_required
def live():
    return render_template("live_feed.html")


if __name__ == "__main__":
    app.run(debug=True)
