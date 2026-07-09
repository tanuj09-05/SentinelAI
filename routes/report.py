import sqlite3
from flask import Blueprint, send_file
from flask_login import login_required, current_user
from config import DATABASE_PATH
from core.camera_manager import CameraManager
from reports.pdf_report import generate_report

report_bp = Blueprint("report", __name__)

@report_bp.route("/generate-report")
@login_required
def generate_pdf_report():
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM events WHERE user_id = ?", (current_user.id,))
        total_events = cursor.fetchone()[0]

        cursor.execute("SELECT id, event_type, timestamp, image_path FROM events WHERE user_id = ? ORDER BY id DESC LIMIT 5", (current_user.id,))
        recent_alerts = cursor.fetchall()

        cursor.execute("SELECT image_path FROM events WHERE user_id = ? AND image_path IS NOT NULL AND image_path != '' ORDER BY id DESC LIMIT 1", (current_user.id,))
        latest_image_row = cursor.fetchone()

    latest_evidence_image = latest_image_row[0] if latest_image_row else None
    filename = "reports/security_report.pdf"
    status = CameraManager.get_thread(current_user.id).get_status()

    generate_report(
        filename=filename,
        total_events=total_events,
        threat_level=status["threat"],
        people_detected=status["people"],
        camera_status=status["camera"],
        latest_evidence_image=latest_evidence_image,
        recent_alerts=recent_alerts,
    )

    return send_file(filename, as_attachment=True)
