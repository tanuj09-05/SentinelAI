import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def generate_report(
    filename,
    total_events,
    threat_level,
    people_detected,
    camera_status="ONLINE",
    latest_evidence_image=None,
    recent_alerts=None,
):
    document = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b><font size=24 color='#2c3e50'>SentinelAI Security Report</font></b>", styles["Title"]))
    elements.append(Spacer(1, 15))

    now = datetime.now()
    elements.append(Paragraph(f"<b>Generated :</b> {now.strftime('%d-%m-%Y %I:%M:%S %p')}", styles["BodyText"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>System Status</b>", styles["Heading2"]))

    table_data = [
        ["Camera Status", camera_status],
        ["Threat Level", threat_level],
        ["People Detected", str(people_detected)],
        ["Total Events", str(total_events)],
    ]

    table = Table(table_data, colWidths=[180, 180])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
        ])
    )

    elements.append(table)
    elements.append(Spacer(1, 25))

    if latest_evidence_image and os.path.exists(latest_evidence_image):
        elements.append(Paragraph("<b>Latest Evidence</b>", styles["Heading2"]))
        elements.append(Image(latest_evidence_image, width=350, height=220))
        elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Summary</b>", styles["Heading2"]))

    summary = f"""
    SentinelAI detected <b>{total_events}</b> total events.

    Current threat level is <b>{threat_level}</b>.

    People currently detected: <b>{people_detected}</b>.
    """

    elements.append(Paragraph(summary, styles["BodyText"]))
    elements.append(Spacer(1, 30))

    if recent_alerts:
        elements.append(Paragraph("<b>Recent Alerts</b>", styles["Heading2"]))
        alerts_table_data = [["ID", "Event Type", "Name", "Timestamp"]]

        for alert in recent_alerts:
            alert_id = str(alert[0])
            event_type = str(alert[1])
            timestamp = str(alert[2])
            track_id = f"#{alert[4]}" if len(alert) > 4 and alert[4] is not None else "N/A"
            rec_name = str(alert[8]) if len(alert) > 8 and alert[8] else "Unknown"

            alerts_table_data.append([alert_id, f"{event_type} ({track_id})", rec_name, timestamp])

        alerts_table = Table(alerts_table_data, colWidths=[50, 150, 100, 100])
        alerts_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ])
        )

        elements.append(alerts_table)
        elements.append(Spacer(1, 25))

    elements.append(Paragraph("<font color='grey'>Generated automatically by SentinelAI v1.0</font>", styles["Italic"]))
    document.build(elements)
