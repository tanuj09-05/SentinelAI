import os
import sqlite3
import numpy as np
from datetime import datetime

os.environ["MXNET_CUDNN_AUTOTUNE_DEFAULT"] = "0"
import warnings
warnings.filterwarnings("ignore")

from insightface.app import FaceAnalysis
from config import DATABASE_PATH

class FaceManager:
    def __init__(self):
        print("[INFO] Initializing InsightFace model...")
        self.app = FaceAnalysis(name="buffalo_l")
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self.known_faces = {}
        self.load_database()
        print("[INFO] InsightFace model initialized successfully.")

    def load_database(self):
        self.known_faces = {}
        try:
            with sqlite3.connect(DATABASE_PATH, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, user_id, name, embedding FROM faces")
                for row in cursor.fetchall():
                    face_id, user_id, name, embedding_blob = row
                    embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                    
                    if user_id not in self.known_faces:
                        self.known_faces[user_id] = {}
                        
                    self.known_faces[user_id][face_id] = {
                        "name": name,
                        "embedding": embedding,
                    }
        except Exception as e:
            print(f"[FaceManager] Error loading database: {e}")

    def add_face(self, user_id, name, frame, photo_path=""):
        faces = self.app.get(frame)
        if not faces:
            return False, "No face detected in the image."

        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        embedding = face.embedding

        try:
            with sqlite3.connect(DATABASE_PATH, timeout=5) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO faces (user_id, name, embedding, photo_path, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, embedding.tobytes(), photo_path, timestamp),
                )
                conn.commit()
        except Exception as e:
            return False, f"Database error: {e}"

        self.load_database()
        return True, "Face registered successfully."

    def match_face(self, user_id, frame, crop_box=None):
        if crop_box is not None:
            x1, y1, x2, y2 = map(int, crop_box)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                return None, 0.0

            person_crop = frame[y1:y2, x1:x2]
            if person_crop.size == 0:
                return None, 0.0
                
            faces = self.app.get(person_crop)
        else:
            faces = self.app.get(frame)

        if not faces:
            return None, 0.0

        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return self._match_embedding(user_id, face.embedding)

    def _match_embedding(self, user_id, query_emb, threshold=0.5):
        if user_id not in self.known_faces or not self.known_faces[user_id]:
            return None, 0.0

        best_match = None
        best_sim = -1.0
        norm_query = np.linalg.norm(query_emb)
        
        if norm_query == 0:
            return None, 0.0

        for face_id, data in self.known_faces[user_id].items():
            db_emb = data["embedding"]
            norm_db = np.linalg.norm(db_emb)
            
            if norm_db == 0:
                continue

            sim = np.dot(query_emb, db_emb) / (norm_query * norm_db)
            if sim > best_sim:
                best_sim = sim
                best_match = data["name"]

        if best_sim > threshold:
            return best_match, float(best_sim)
            
        return None, float(best_sim)

_face_manager_instance = None

def get_face_manager():
    global _face_manager_instance
    if _face_manager_instance is None:
        try:
            _face_manager_instance = FaceManager()
        except Exception as e:
            print(f"[WARN] Failed to initialize FaceManager: {e}")
            _face_manager_instance = None
    return _face_manager_instance
