from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from database.user import create_user, get_user_by_email, verify_password
from core.camera_manager import CameraManager

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required", "error")
            return redirect(url_for("auth.signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("auth.signup"))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.signup"))

        if not create_user(name, email, password):
            flash("Email already exists", "error")
            return redirect(url_for("auth.signup"))

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") is not None

        if not email or not password:
            flash("Email and password are required", "error")
            return redirect(url_for("auth.login"))

        user_data = get_user_by_email(email)

        if not user_data:
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        user_id, name, user_email, password_hash, _ = user_data

        if not verify_password(password_hash, password):
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        user = User(user_id, name, user_email)
        login_user(user, remember=remember)

        CameraManager.get_thread(user.id)

        flash(f"Welcome back, {name}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("landing_page"))

class User:
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
