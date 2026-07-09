import cv2
import time
from threading import Thread, Lock
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from config import RESTRICTED_ZONE
from core.detector import detect
from core.event_engine import check_intrusion
from core.alert_manager import save_intrusion_image
from core.email_alert import send_intrusion_email
from database.database import save_event, DATABASE_PATH
import sqlite3
from database.user import get_user_settings


class UserCameraThread(Thread):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.daemon = True
        self.last_accessed = time.time()
        self.latest_jpeg = None
        
        self.latest_status = {
            "people": 0,
            "intrusion": False,
            "camera": "offline",
            "latency": 0,
            "fps": 0,
            "loitering_alert": False,
            "max_people": 0,
        }

        self.running = True
        self.active_zone_tracks = {}
        self.loitering_alerted = set()
        self.recognized_faces = {}
        self.recognition_attempts = {}
        self.recognition_in_progress = set()
        self._last_processed_frame_id = None

        self._black_frame = self._generate_black_frame()
        self.latest_jpeg = self._black_frame

        self._latest_raw_frame = None
        self._capture_running = False
        self._capture_thread = None

        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cache_total_events()

    def _cache_total_events(self):
        try:
            with sqlite3.connect(DATABASE_PATH, timeout=5) as db_connection:
                database_cursor = db_connection.cursor()
                database_cursor.execute(
                    "SELECT COUNT(*) FROM events WHERE user_id = ?", (self.user_id,)
                )
                self.latest_status["total_events"] = database_cursor.fetchone()[0]
        except Exception:
            self.latest_status["total_events"] = 0

    def _increment_total_events(self):
        if "total_events" in self.latest_status:
            self.latest_status["total_events"] += 1

    def _generate_black_frame(self, text="Camera Loading..."):
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            black_image,
            text,
            (180, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (80, 80, 80),
            2,
        )
        _, jpeg_buffer = cv2.imencode(".jpg", black_image)
        return jpeg_buffer.tobytes()

    def run(self):
        user_settings = get_user_settings(self.user_id)

        if not user_settings:
            self.latest_status["camera"] = "ERROR: No Settings"
            self.latest_jpeg = self._generate_black_frame("No Camera Settings")
            self.running = False
            return

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

        camera_path = rtsp_url if camera_source == "rtsp" else (camera_index or 0)
        camera = cv2.VideoCapture(camera_path)

        if not camera.isOpened():
            self.latest_status["camera"] = "OFFLINE"
            self.latest_jpeg = self._generate_black_frame("Camera Offline")
            self.running = False
            return

        self.latest_status["camera"] = "online"
        self._capture_running = True
        self._capture_thread = Thread(
            target=self._capture_loop, args=(camera,), daemon=True
        )
        self._capture_thread.start()

        frame_count = 0
        last_fps_time = time.time()

        while self.running:
            start_time = time.time()

            if time.time() - self.last_accessed > 15:
                break

            current_frame = self._latest_raw_frame

            if current_frame is None or id(current_frame) == self._last_processed_frame_id:
                time.sleep(0.01)
                continue
            
            self._last_processed_frame_id = id(current_frame)
            processing_frame = current_frame.copy()
            self.latest_status["camera"] = "online"

            processing_frame, total_people, bounding_boxes, track_ids = detect(
                processing_frame
            )

            self.latest_status["people"] = total_people
            self.latest_status["max_people"] = max(
                self.latest_status.get("max_people", 0), total_people
            )

            self._draw_faces_and_dispatch(processing_frame, bounding_boxes, track_ids)
            self._draw_restricted_zone(processing_frame)
            self._handle_intrusions_and_loitering(
                processing_frame, bounding_boxes, track_ids
            )
            self._handle_exits(track_ids)
            self._cleanup_old_faces(track_ids)

            _, jpeg_buffer = cv2.imencode(".jpg", processing_frame)
            self.latest_jpeg = jpeg_buffer.tobytes()

            latency_ms = int((time.time() - start_time) * 1000)
            self.latest_status["latency"] = latency_ms

            frame_count += 1
            if time.time() - last_fps_time >= 1.0:
                self.latest_status["fps"] = frame_count
                frame_count = 0
                last_fps_time = time.time()

        self._capture_running = False
        camera.release()
        self.executor.shutdown(wait=False)
        self.running = False

    def _draw_faces_and_dispatch(self, frame, bounding_boxes, track_ids):
        for box, track_id in zip(bounding_boxes, track_ids):
            if track_id not in self.recognized_faces and track_id not in self.recognition_in_progress:
                attempts = self.recognition_attempts.get(track_id, 0)
                if attempts < 10:
                    self.recognition_in_progress.add(track_id)
                    self.executor.submit(
                        self._async_recognize_face, track_id, frame.copy(), box
                    )
                else:
                    self.recognized_faces[track_id] = {
                        "name": "UNKNOWN PERSON",
                        "conf": 0.0,
                        "is_known": False,
                    }

            if track_id in self.recognized_faces:
                face_info = self.recognized_faces[track_id]
                x1, y1, x2, y2 = map(int, box)

                label_text = (
                    f"{face_info['name']} ({face_info['conf']:.2f})"
                    if face_info["conf"] > 0
                    else face_info["name"]
                )

                text_color = (255, 255, 0) if face_info["is_known"] else (0, 165, 255)
                cv2.putText(
                    frame,
                    label_text,
                    (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    text_color,
                    2,
                )

    def _async_recognize_face(self, track_id, frame, box):
        try:
            from core.face_manager import get_face_manager
            face_manager = get_face_manager()
            if not face_manager:
                return

            recognized_name, confidence = face_manager.match_face(
                self.user_id, frame, crop_box=box
            )

            if recognized_name:
                self.recognized_faces[track_id] = {
                    "name": recognized_name,
                    "conf": confidence,
                    "is_known": True,
                }
            elif confidence > 0.0:
                self.recognized_faces[track_id] = {
                    "name": "UNKNOWN PERSON",
                    "conf": confidence,
                    "is_known": False,
                }
                
            self.recognition_attempts[track_id] = self.recognition_attempts.get(track_id, 0) + 1
        finally:
            if track_id in self.recognition_in_progress:
                self.recognition_in_progress.remove(track_id)

    def _draw_restricted_zone(self, frame):
        zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 0, 255), 2)
        cv2.putText(
            frame,
            "Restricted Zone",
            (zone_x1, zone_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    def _handle_intrusions_and_loitering(self, frame, bounding_boxes, track_ids):
        intruding_ids = check_intrusion(bounding_boxes, track_ids)
        self.latest_status["intrusion"] = len(intruding_ids) > 0

        current_time = time.time()
        loitering_active = False

        for track_id in intruding_ids:
            default_face = {"name": "UNKNOWN (No Face)", "is_known": False}
            face_info = self.recognized_faces.get(track_id, default_face)
            recognized_name = face_info["name"]
            is_known = face_info["is_known"]

            if track_id not in self.active_zone_tracks:
                self.active_zone_tracks[track_id] = current_time
                entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.executor.submit(
                    self._save_and_alert_event,
                    frame.copy(),
                    track_id,
                    "Intrusion",
                    recognized_name,
                    is_known,
                    entry_time=entry_timestamp,
                )

            time_in_zone = current_time - self.active_zone_tracks[track_id]

            if time_in_zone > 15:
                loitering_active = True
                cv2.putText(
                    frame,
                    f"LOITERING ({recognized_name})",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3,
                )

                if track_id not in self.loitering_alerted:
                    self.loitering_alerted.add(track_id)

                    self.executor.submit(
                        self._save_and_alert_event,
                        frame.copy(),
                        track_id,
                        "Loitering",
                        recognized_name,
                        is_known,
                        duration=time_in_zone,
                    )
            else:
                if self.latest_status["intrusion"]:
                    cv2.putText(
                        frame,
                        "INTRUSION DETECTED",
                        (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 165, 255),
                        3,
                    )

        self.latest_status["loitering_alert"] = loitering_active

        if loitering_active:
            self.latest_status["threat"] = "CRITICAL"
        elif self.latest_status["intrusion"]:
            self.latest_status["threat"] = "HIGH"
        else:
            self.latest_status["threat"] = "SAFE"

    def _handle_exits(self, track_ids):
        current_time = time.time()
        zone_tracks = list(self.active_zone_tracks.keys())

        for track_id in zone_tracks:
            if track_id not in track_ids:
                duration = current_time - self.active_zone_tracks[track_id]

                default_face = {"name": "UNKNOWN (No Face)", "is_known": False}
                face_info = self.recognized_faces.get(track_id, default_face)

                self.executor.submit(
                    self._save_and_alert_event,
                    None,
                    track_id,
                    "Zone Exit",
                    face_info["name"],
                    face_info["is_known"],
                    duration=duration,
                )

                del self.active_zone_tracks[track_id]

                if track_id in self.loitering_alerted:
                    self.loitering_alerted.remove(track_id)

    def _cleanup_old_faces(self, current_track_ids):
        active_tids = set(current_track_ids)

        for track_id in list(self.recognized_faces.keys()):
            if track_id not in active_tids and track_id not in self.active_zone_tracks:
                del self.recognized_faces[track_id]

    def _save_and_alert_event(
        self,
        frame,
        track_id,
        event_type,
        recognized_name,
        is_known,
        entry_time=None,
        duration=None,
    ):
        image_path = ""
        if frame is not None:
            image_path = save_intrusion_image(frame)

        exit_time = None
        if event_type == "Zone Exit":
            exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_event(
            self.user_id,
            event_type,
            image_path,
            track_id=track_id,
            entry_time=entry_time,
            exit_time=exit_time,
            duration=duration,
            recognized_name=recognized_name,
            is_known=is_known,
        )

        self._increment_total_events()

        if not is_known and event_type in ["Intrusion", "Loitering"]:
            threat = "CRITICAL" if event_type == "Loitering" else "HIGH"
            send_intrusion_email(
                self.user_id, image_path, threat, 1, track_id, recognized_name, is_known
            )

    def _capture_loop(self, camera):
        while self._capture_running:
            success, frame = camera.read()
            if success:
                self._latest_raw_frame = frame
            else:
                self._latest_raw_frame = None
                time.sleep(1)

    def get_jpeg(self):
        self.last_accessed = time.time()
        return self.latest_jpeg

    def get_status(self):
        self.last_accessed = time.time()
        return self.latest_status


class CameraManager:
    _threads = {}
    _lock = Lock()

    @classmethod
    def get_thread(cls, user_id):
        with cls._lock:
            if user_id not in cls._threads or not cls._threads[user_id].running:
                new_thread = UserCameraThread(user_id)
                new_thread.start()
                cls._threads[user_id] = new_thread
            return cls._threads[user_id]
