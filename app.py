from flask import Flask, render_template, Response, jsonify, request
import sqlite3
import json
from flask import send_file
import cv2
from reports.pdf_report import generate_report
from core.alert_manager import save_intrusion_image
from core.email_alert import send_intrusion_email
from core.camera import Camera
from core.detector import detect
from core.event_engine import check_intrusion
from config import DATABASE_PATH, RESTRICTED_ZONE
from database.database import save_event
from core.threat_engine import calculate_threat
from routes.report import report_bp
from core.system_state import SYSTEM_STATE
from routes.api import api_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.register_blueprint(report_bp)

camera = Camera()
intrusion_active = False
app.register_blueprint(api_bp)
# These values let the dashboard status endpoint reuse the latest
# detection result without reading a second frame from the camera.
latest_people_count = 0
latest_intrusion_state = False
latest_threat_level = "SAFE"


def generate_frames():
    global intrusion_active
    global latest_people_count
    global latest_intrusion_state
    global latest_threat_level

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Run YOLO Detection
        frame, person_count, boxes = detect(frame)

        # Keep the latest values in memory so /api/status can return them
        # without reading the camera a second time.
        latest_people_count = person_count

        # Restricted Zone
        zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE

        cv2.rectangle(
            frame,
            (zone_x1, zone_y1),
            (zone_x2, zone_y2),
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            "Restricted Zone",
            (zone_x1, zone_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

        # Check Intrusion
        intrusion_detected = check_intrusion(boxes)
        latest_intrusion_state = intrusion_detected

        latest_threat_level = calculate_threat(
            person_count,
            intrusion_detected
        )

        SYSTEM_STATE["people"] = person_count

        SYSTEM_STATE["intrusion"] = intrusion_detected

        SYSTEM_STATE["threat"] = latest_threat_level
        SYSTEM_STATE["camera"] = "ONLINE"

        if intrusion_detected:

            cv2.putText(
                frame,
                "INTRUSION DETECTED",
                (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

            # Save alert only once while the intrusion is active.
            if not intrusion_active:

                intrusion_active = True

                filename = save_intrusion_image(frame)

                save_event(
                    "Intrusion",
                    filename
                )

                # Send the intrusion email in the background so the
                # video stream does not block while the message is sent.
                from threading import Thread

                email_thread = Thread(
                    target=send_intrusion_email,
                    args=(filename, latest_threat_level, person_count),
                    daemon=True
                )
                email_thread.start()

                print("[ALERT] Intrusion Detected")

        else:

            intrusion_active = False

        # Convert frame to JPEG
        _, buffer = cv2.imencode(".jpg", frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )


@app.route("/")
def landing_page():

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM events ORDER BY id DESC"
    )
    events = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM events"
    )
    total_events = cursor.fetchone()[0]

    latest_event = events[0] if events else None

    connection.close()

    return render_template(
        "dashboard.html",
        events=events,
        total_events=total_events,
        latest_event=latest_event
    )


@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/api/status")
def api_status():
    return jsonify({
        "camera": "ONLINE",
        "people": latest_people_count,
        "intrusion": latest_intrusion_state,
        "threat": latest_threat_level
    })


@app.route("/api/alerts")
def api_alerts():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, event_type, timestamp
        FROM events
        ORDER BY id DESC
        LIMIT 10
    """)

    alerts = cursor.fetchall()

    connection.close()

    return jsonify([
        {
            "id": row[0],
            "event": row[1],
            "time": row[2]
        }
        for row in alerts
    ])

@app.route("/api/analytics")
def api_analytics():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DATE(timestamp), COUNT(*)
        FROM events
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
    """)

    rows = cursor.fetchall()

    connection.close()

    labels = []
    values = []

    for row in rows:

        labels.append(row[0])
        values.append(row[1])

    return jsonify({
        "labels": labels,
        "values": values
    })

@app.route("/api/search")
def api_search():

    keyword = request.args.get("q", "")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM events
        WHERE event_type LIKE ?
           OR timestamp LIKE ?
        ORDER BY id DESC
    """, (

        f"%{keyword}%",

        f"%{keyword}%"

    ))

    rows = cursor.fetchall()

    connection.close()

    return jsonify(rows)




@app.route("/analytics")
def analytics():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DATE(timestamp), COUNT(*)
        FROM events
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
        """
    )
    daily_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT DATE(timestamp), COUNT(*)
        FROM events
        WHERE DATE(timestamp) >= DATE('now', '-6 day')
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
        """
    )
    weekly_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT strftime('%Y-%m', timestamp), COUNT(*)
        FROM events
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY strftime('%Y-%m', timestamp)
        """
    )
    monthly_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT event_type, COUNT(*)
        FROM events
        GROUP BY event_type
        ORDER BY COUNT(*) DESC
        """
    )
    event_type_rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "analytics.html",
        total_events=total_events,
        people_detected=SYSTEM_STATE["people"],
        threat_level=SYSTEM_STATE["threat"],
        camera_status=SYSTEM_STATE["camera"],
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
def alerts():
    keyword = request.args.get("q", "").strip()
    selected_event_type = request.args.get("event_type", "All")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    if page < 1:
        page = 1

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT DISTINCT event_type FROM events ORDER BY event_type ASC"
    )
    event_types = [row[0] for row in cursor.fetchall()]

    conditions = []
    parameters = []

    if keyword:
        conditions.append("(event_type LIKE ? OR timestamp LIKE ?)")
        parameters.extend([f"%{keyword}%", f"%{keyword}%"])

    if selected_event_type != "All":
        conditions.append("event_type = ?")
        parameters.append(selected_event_type)

    where_clause = ""
    if conditions:
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

    connection.close()

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

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT DISTINCT event_type FROM events ORDER BY event_type ASC"
    )
    event_types = [row[0] for row in cursor.fetchall()]

    query = "SELECT id, event_type, timestamp, image_path FROM events"
    conditions = []
    parameters = []

    if keyword:
        conditions.append("(event_type LIKE ? OR timestamp LIKE ?)")
        parameters.extend([f"%{keyword}%", f"%{keyword}%"])

    if selected_event_type != "All":
        conditions.append("event_type = ?")
        parameters.append(selected_event_type)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY {selected_sort_column} {selected_sort_order}"

    cursor.execute(query, parameters)
    events = cursor.fetchall()

    connection.close()

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
def live():
    return render_template("live_feed.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(debug=True)