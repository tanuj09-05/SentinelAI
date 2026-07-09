import os
import sqlite3
import cv2
import uuid
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from database.database import DATABASE_PATH
from core.face_manager import get_face_manager

faces_bp = Blueprint("faces_bp", __name__)

UPLOAD_FOLDER = "static/faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@faces_bp.route("/faces", methods=["GET"])
@login_required
def faces_page():
    user_id = current_user.get_id()
    faces = []
    
    try:
        with sqlite3.connect(DATABASE_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, photo_path, created_at FROM faces WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            faces = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching faces: {e}")

    return render_template("faces.html", faces=faces)

@faces_bp.route("/api/faces/upload", methods=["POST"])
@login_required
def upload_face():
    user_id = current_user.get_id()

    if "file" not in request.files or "name" not in request.form:
        return jsonify({"success": False, "message": "Missing file or name."}), 400

    file = request.files["file"]
    name = request.form["name"].strip()

    if not file.filename:
        return jsonify({"success": False, "message": "No selected file."}), 400

    if not name:
        return jsonify({"success": False, "message": "Name is required."}), 400

    ext = os.path.splitext(secure_filename(file.filename))[1]
    filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{ext}")
    file.save(filepath)

    img = cv2.imread(filepath)
    if img is None:
        os.remove(filepath)
        return jsonify({"success": False, "message": "Invalid image file."}), 400

    fm = get_face_manager()
    if not fm:
        os.remove(filepath)
        return jsonify({"success": False, "message": "Face Manager is not initialized."}), 500

    success, msg = fm.add_face(user_id, name, img, filepath)

    if not success:
        os.remove(filepath)
        return jsonify({"success": False, "message": msg}), 400

    return jsonify({"success": True, "message": "Face registered successfully!"})

@faces_bp.route("/api/faces/<int:face_id>", methods=["DELETE"])
@login_required
def delete_face(face_id):
    user_id = current_user.get_id()

    try:
        with sqlite3.connect(DATABASE_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT photo_path FROM faces WHERE id = ? AND user_id = ?", (face_id, user_id))
            row = cursor.fetchone()
            
            if row and row[0] and os.path.exists(row[0]):
                os.remove(row[0])

            cursor.execute("DELETE FROM faces WHERE id = ? AND user_id = ?", (face_id, user_id))
            conn.commit()

            fm = get_face_manager()
            if fm:
                fm.load_database()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
