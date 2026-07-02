import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from database.user import get_user_settings


import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from database.user import get_user_settings


def _validate_settings(user_settings):
    """
    Purpose:
    Check krna ki email bhejane ke liye zaruri settings database me hain ya nahi.
    """
    if not user_settings:
        print("[WARN] Email alert nhi bheja kyunki user settings database me nhi mili.")
        return False, None

    # Tuple unpacking: Database se saari settings variables me daal rhe hain
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

    # Agar koi ek setting bhi gayab (missing) hai toh email nhi bhej sakte
    if not smtp_host or not smtp_username or not smtp_password or not receiver_email:
        print(
            "[WARN] Email alert cancel. "
            "Kripya Settings page me jaakar SMTP host, username, password aur receiver email theek se bharein."
        )
        return False, None

    # Try karenge ki port integer me convert ho jaye
    try:
        final_smtp_port = int(smtp_port) if smtp_port is not None else 587
    except (TypeError, ValueError):
        print(f"[WARN] Email alert cancel. SMTP port invalid hai: {smtp_port}")
        return False, None

    # Sab kuch theek hai, ab in settings ko dictionary me return kr denge
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
    """
    Purpose:
    Email ka body text aur subject banana.
    """
    current_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    email = EmailMessage()
    email["Subject"] = f"SentinelAI Intrusion Alert - {threat_level}"
    email["From"] = email_details["sender_email"]
    email["To"] = email_details["receiver_email"]

    # Ternary operators (if/else ek line me) se choti conditions handle kr rhe hain
    status_text = "Known Person" if is_known else "Unknown Person"
    name_text = recognized_name if recognized_name else "Unknown"
    track_text = f"#{track_id}" if track_id is not None else "N/A"

    # Email ka main text set kr rhe hain
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
    """
    Purpose:
    Bane hue email me evidence photo attach krna.
    """
    # Image read krne ke liye 'rb' (read binary) mode me open krte hain
    with open(image_path, "rb") as image_file:
        binary_image_data = image_file.read()

    # File ka aakhri naam nikalne ke liye (eg: "alerts/photo.jpg" -> "photo.jpg")
    image_filename = os.path.basename(image_path)

    # Data ko email me attach kr rhe hain
    email.add_attachment(
        binary_image_data, maintype="image", subtype="jpeg", filename=image_filename
    )


def _send_email_via_smtp(email, email_details):
    """
    Purpose:
    Smtplib library ka use krke finally server pr email bhejna.
    """
    try:
        # Context manager 'with' use kr rhe hain taaki email bhejne ke baad connection khud close ho jaye
        with smtplib.SMTP(
            email_details["smtp_host"], email_details["smtp_port"], timeout=30
        ) as smtp_server:
            # Connection ko secure banane ke liye TLS start kr rhe hain
            smtp_server.starttls()

            # Login krke email send kr rhe hain
            smtp_server.login(
                email_details["smtp_username"], email_details["smtp_password"]
            )
            smtp_server.send_message(email)

        print(
            f"[ALERT] Email successfully bhej diya gaya: {email_details['receiver_email']}"
        )
        return True

    # Niche alag-alag type ke errors ko handle kiya gaya hai taaki application crash na ho
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
    """
    Purpose:
    Jab intrusion detect ho, tab yeh main function alert email bhejta hai.
    """
    # 1. User ki settings DB se lani hai
    user_settings = get_user_settings(user_id)

    # 2. Settings validate krni hai
    is_valid, email_details = _validate_settings(user_settings)
    if not is_valid:
        return False

    # 3. Check krna hai ki evidence image asal me hard drive par exist krti hai ya nahi
    if not os.path.exists(image_path):
        print(f"[WARN] Email alert nhi gaya kyunki image exist nhi krti: {image_path}")
        return False

    # 4. Email banana aur message dalna
    email = _create_email_message(
        threat_level,
        people_count,
        track_id,
        recognized_name,
        is_known,
        image_path,
        email_details,
    )

    # 5. Usme evidence image attach krna
    _attach_evidence_image(email, image_path)

    # 6. SMTP server ke through send krna
    return _send_email_via_smtp(email, email_details)
