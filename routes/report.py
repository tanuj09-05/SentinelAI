from flask import Blueprint, send_file
import sqlite3
from core.system_state import SYSTEM_STATE

from reports.pdf_report import generate_report
from config import DATABASE_PATH

report_bp = Blueprint("report", __name__)




@report_bp.route("/generate-report")
def generate_pdf_report():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT id, event_type, timestamp, image_path
        FROM events
        ORDER BY id DESC
        LIMIT 5
        """
    )
    recent_alerts = cursor.fetchall()

    cursor.execute(
        """
        SELECT image_path
        FROM events
        WHERE image_path IS NOT NULL AND image_path != ''
        ORDER BY id DESC
        LIMIT 1
        """
    )
    latest_image_row = cursor.fetchone()

    latest_evidence_image = None

    if latest_image_row:
        latest_evidence_image = latest_image_row[0]

    connection.close()

    filename = "reports/security_report.pdf"

    generate_report(
        filename=filename,
        total_events=total_events,
        threat_level=SYSTEM_STATE["threat"],
        people_detected=SYSTEM_STATE["people"],
        camera_status=SYSTEM_STATE["camera"],
        latest_evidence_image=latest_evidence_image,
        recent_alerts=recent_alerts,
    )

    return send_file(
        filename,
        as_attachment=True
    )