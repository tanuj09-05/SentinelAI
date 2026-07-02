import smtplib
from email.message import EmailMessage
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from database.user import ensure_user_settings, save_user_settings

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def validate_smtp(host, port, username, password):
    try:
        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.starttls()
            server.login(username, password)
        return True, "SMTP connection successful."
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your App Password or Username."
    except Exception as e:
        return False, f"Failed to connect to SMTP server: {e}"


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def settings():
    """
    Handle user settings page.
    GET: Display current settings
    POST: Save updated settings
    """
    user_id = current_user.id
    existing_settings = ensure_user_settings(user_id)

    if request.method == "POST":
        # Get form data. Default to Gmail if not provided (from basic UI).
        app_password = request.form.get("app_password", "").strip()

        # Advanced settings
        smtp_host = request.form.get("smtp_host", "smtp.gmail.com").strip()
        smtp_port_str = request.form.get("smtp_port", "587").strip()
        smtp_username = request.form.get("smtp_username", current_user.email).strip()
        sender_email = request.form.get("sender_email", current_user.email).strip()

        # Receiver email logic
        use_custom_receiver = request.form.get("use_custom_receiver") == "on"
        custom_receiver_email = request.form.get("custom_receiver_email", "").strip()
        receiver_email = (
            custom_receiver_email
            if use_custom_receiver and custom_receiver_email
            else current_user.email
        )

        # Camera settings
        camera_source = request.form.get("camera_source", "index").strip()
        camera_index_str = request.form.get("camera_index", "0").strip()
        rtsp_url = request.form.get("rtsp_url", "").strip()

        # Validate SMTP port
        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            flash("SMTP port must be a valid number", "error")
            return redirect(url_for("settings.settings"))

        # Validate camera index
        try:
            camera_index = int(camera_index_str)
        except ValueError:
            flash("Camera index must be a valid number", "error")
            return redirect(url_for("settings.settings"))

        # Determine password to use
        smtp_password = (
            app_password
            if app_password
            else (existing_settings[5] if existing_settings else "")
        )

        # Validate email settings if SMTP is configured
        if smtp_password:
            is_valid, msg = validate_smtp(
                smtp_host, smtp_port, smtp_username, smtp_password
            )
            if not is_valid:
                flash(msg, "error")
                return redirect(url_for("settings.settings"))
        elif app_password:  # if they tried to set one but it's empty somehow
            flash(
                "App Password cannot be empty if you intend to enable email alerts.",
                "error",
            )
            return redirect(url_for("settings.settings"))

        # Validate camera source
        if camera_source not in ["index", "rtsp"]:
            flash("Invalid camera source", "error")
            return redirect(url_for("settings.settings"))

        # If RTSP is selected, require RTSP URL
        if camera_source == "rtsp" and not rtsp_url:
            flash("RTSP URL is required when using RTSP camera source", "error")
            return redirect(url_for("settings.settings"))

        # Save settings to database
        save_user_settings(
            user_id,
            smtp_host,
            smtp_port,
            smtp_username,
            smtp_password,
            sender_email,
            receiver_email,
            camera_source,
            camera_index,
            rtsp_url,
        )

        flash("Settings saved successfully", "success")
        return redirect(url_for("settings.settings"))

    # GET Request: Fetch settings to display
    if not existing_settings:
        settings_data = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": current_user.email,
            "smtp_password": "",
            "sender_email": current_user.email,
            "receiver_email": current_user.email,
            "camera_source": "index",
            "camera_index": 0,
            "rtsp_url": "",
        }
    else:
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
        ) = existing_settings

        settings_data = {
            "smtp_host": smtp_host or "smtp.gmail.com",
            "smtp_port": smtp_port or 587,
            "smtp_username": smtp_username or current_user.email,
            "smtp_password": smtp_password or "",
            "sender_email": sender_email or current_user.email,
            "receiver_email": receiver_email or current_user.email,
            "camera_source": camera_source or "index",
            "camera_index": camera_index or 0,
            "rtsp_url": rtsp_url or "",
        }

    return render_template("settings.html", settings=settings_data, user=current_user)


@settings_bp.route("/test_email", methods=["POST"])
@login_required
def test_email():
    """
    Send a test email using the currently saved settings.
    """
    user_settings = ensure_user_settings(current_user.id)
    if not user_settings:
        return (
            jsonify(
                {"success": False, "message": "No settings found. Save settings first."}
            ),
            400,
        )

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

    if not smtp_password:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "App Password is not set. Please save settings first.",
                }
            ),
            400,
        )

    try:
        message = EmailMessage()
        message["Subject"] = "SentinelAI - Test Email"
        message["From"] = sender_email if sender_email else smtp_username
        message["To"] = receiver_email
        message.set_content(
            "This is a test email from your SentinelAI Command Center. Your email alerts are configured correctly!"
        )

        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        return jsonify({"success": True, "message": "Test email sent successfully!"})
    except smtplib.SMTPAuthenticationError:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Authentication failed. Check your App Password.",
                }
            ),
            401,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Failed to send test email: {str(e)}"}
            ),
            500,
        )
