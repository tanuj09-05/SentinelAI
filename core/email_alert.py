import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from database.user import get_user_settings

def _validate_settings(user_settings):
    if not user_settings:
        print("[WARN] Email alert nhi bheja kyunki user settings database me nhi mili.")
        return False, None

    (
        settings_id,
        settings_user_id,
        smtp_host,
        smtp_port,
        smtp_username,
        smtp_password,
        sender_email,
        receiver_email,
        camera_source,
        camera_index,
        rtsp_url,
        created_at,
        updated_at,
    ) = user_settings

    if not smtp_host or not smtp_username or not smtp_password or not receiver_email:
        print(
            "[WARN] Email alert cancel. "
            "Kripya Settings page me jaakar SMTP host, username, password aur receiver email theek se bharein."
        )
        return False, None

    try:
        final_smtp_port = int(smtp_port) if smtp_port is not None else 587
    except (TypeError, ValueError):
        print(f"[WARN] Email alert cancel. SMTP port invalid hai: {smtp_port}")
        return False, None

    return True, {
        "smtp_host": smtp_host,
        "smtp_port": final_smtp_port,
        "smtp_username": smtp_username,
        "smtp_password": smtp_password,
        "sender_email": sender_email if sender_email else smtp_username,
        "receiver_email": receiver_email,
    }

def _create_email_message(
    threat_level,
    people_count,
    track_id,
    recognized_name,
    is_known,
    image_path,
    email_details,
):
    current_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    email = EmailMessage()
    email["Subject"] = f"SentinelAI Intrusion Alert - {threat_level}"
    email["From"] = email_details["sender_email"]
    email["To"] = email_details["receiver_email"]

    status_text = "Known Person" if is_known else "Unknown Person"
    name_text = recognized_name if recognized_name else "Unknown"
    track_text = f"#{track_id}" if track_id is not None else "N/A"

    email.set_content(f"""
SentinelAI detected an intrusion.

Time: {current_time_string}
Threat Level: {threat_level}
Track ID: {track_text}
Recognized Name: {name_text} ({status_text})
People Detected: {people_count}
Evidence Image: {image_path}
""".strip())
    return email

def _attach_evidence_image(email, image_path):
    with open(image_path, "rb") as image_file:
        binary_image_data = image_file.read()

    image_filename = os.path.basename(image_path)
    email.add_attachment(
        binary_image_data, maintype="image", subtype="jpeg", filename=image_filename
    )

def _send_email_via_smtp(email, email_details):
    try:
        with smtplib.SMTP(
            email_details["smtp_host"], email_details["smtp_port"], timeout=30
        ) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(
                email_details["smtp_username"], email_details["smtp_password"]
            )
            smtp_server.send_message(email)

        print(
            f"[ALERT] Email successfully bhej diya gaya: {email_details['receiver_email']}"
        )
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[WARN] SMTP login fail ho gaya. Kripya Settings me apna username/password check karein."
        )
        return False
    except smtplib.SMTPException as error:
        print(f"[WARN] SMTP error ke karan email nhi gaya: {error}")
        return False
    except OSError as error:
        print(
            f"[WARN] SMTP server ({email_details['smtp_host']}:{email_details['smtp_port']}) se connect nhi ho paaye. {error}"
        )
        return False
    except Exception as error:
        print(f"[WARN] Email bhejne me anjaan error aayi: {error}")
        return False

def send_intrusion_email(
    user_id,
    image_path,
    threat_level,
    people_count,
    track_id=None,
    recognized_name=None,
    is_known=None,
):
    user_settings = get_user_settings(user_id)

    is_valid, email_details = _validate_settings(user_settings)
    if not is_valid:
        return False

    if not os.path.exists(image_path):
        print(f"[WARN] Email alert nhi gaya kyunki image exist nhi krti: {image_path}")
        return False

    email = _create_email_message(
        threat_level,
        people_count,
        track_id,
        recognized_name,
        is_known,
        image_path,
        email_details,
    )

    _attach_evidence_image(email, image_path)

    return _send_email_via_smtp(email, email_details)
