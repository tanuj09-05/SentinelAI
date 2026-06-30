import os
import smtplib
from email.message import EmailMessage
from datetime import datetime


def send_intrusion_email(image_path, threat_level, people_count):
    """
    Send an intrusion alert email with the latest evidence image attached.

    The function is safe to call even when email settings are missing.
    In that case it returns False and prints a short warning.
    """

    smtp_host = os.getenv("SENTINEL_SMTP_HOST", "")
    smtp_port = int(os.getenv("SENTINEL_SMTP_PORT", "587"))
    smtp_username = os.getenv("SENTINEL_SMTP_USERNAME", "")
    smtp_password = os.getenv("SENTINEL_SMTP_PASSWORD", "")
    email_from = os.getenv("SENTINEL_EMAIL_FROM", smtp_username)
    email_to = os.getenv("SENTINEL_EMAIL_TO", "")

    if not smtp_host or not smtp_username or not smtp_password or not email_to:
        print("[WARN] Email alert not sent because SMTP settings are missing.")
        return False

    if not os.path.exists(image_path):
        print(f"[WARN] Email alert not sent because image was not found: {image_path}")
        return False

    alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = EmailMessage()
    message["Subject"] = f"SentinelAI Intrusion Alert - {threat_level}"
    message["From"] = email_from
    message["To"] = email_to

    message.set_content(
        f"""
SentinelAI detected an intrusion.

Time: {alert_time}
Threat Level: {threat_level}
People Detected: {people_count}
Evidence Image: {image_path}
""".strip()
    )

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    image_name = os.path.basename(image_path)
    message.add_attachment(
        image_data,
        maintype="image",
        subtype="jpeg",
        filename=image_name
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

    print(f"[ALERT] Email sent successfully to {email_to}")
    return True