import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
from config import MODEL_PATH

# Model ko ek hi baar memory me load karenge taaki app fast chale
try:
    yolo_model = YOLO(MODEL_PATH)
    AI_STATUS = "online"
except Exception as error:
    print(f"[ERROR] YOLO model load nhi ho paya: {error}")
    yolo_model = None
    AI_STATUS = "offline"


def get_ai_status():
    """
    Purpose:
    Check krna ki AI (YOLO) sahi se chal rha hai ya nahi.
    """
    return AI_STATUS


# Puraani tracking details save krne ke liye dictionary
movement_history = defaultdict(list)


def draw_bounding_box(frame, box, track_id, confidence):
    """
    Purpose:
    Ek person ke charo taraf box draw krna aur uski ID likhna.
    """
    x1, y1, x2, y2 = map(int, box)

    # Person ke around green box draw kr rhe hain
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Box ke upar tracking ID aur confidence (probability) likh rhe hain
    label = f"ID:{track_id} {confidence:.2f}"
    cv2.putText(
        frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
    )


def calculate_center_point(box):
    """
    Purpose:
    Bounding box ka center (mid-point) nikalna.
    """
    x1, y1, x2, y2 = map(int, box)
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    return center_x, center_y


def draw_tracking_trail(frame, track_id, center_x, center_y):
    """
    Purpose:
    Person ka peeche chhutne wala trail (line) draw krna taaki uska rasta dikhe.
    """
    # Center par ek chota red dot draw kr rhe hain
    cv2.circle(frame, (center_x, center_y), 4, (0, 0, 255), -1)

    # Person ki history me naya point dal rhe hain
    person_path = movement_history[track_id]
    person_path.append((center_x, center_y))

    # Memory full na ho isliye sirf last 20 points hi save rkhenge
    if len(person_path) > 20:
        person_path.pop(0)

    # Agar 2 se zyada points hain tabhi line draw ho sakti hai
    if len(person_path) > 1:
        points_array = np.array(person_path, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(
            frame, [points_array], isClosed=False, color=(0, 255, 255), thickness=2
        )


def detect(frame):
    """
    Purpose:
    Current camera frame me persons detect krna aur unhe track krna.

    Parameters:
    frame -> Camera se aaya hua ek image frame.

    Returns:
    Updated frame jisme boxes draw kiye gaye hain, total number of people, list of boxes, aur unke track IDs.
    """
    # Agar model load nhi hua toh bina kisi error ke return kr denge
    if yolo_model is None:
        return frame, 0, [], []

    # YOLO model ko frame bhej rhe hain. ByteTrack automatically sabko unique IDs de dega.
    detection_results = yolo_model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False,
        imgsz=320,
        conf=0.4,
        classes=[0],
        half=False,
    )

    person_count = 0
    detected_boxes = []
    detected_track_ids = []

    # Agar frame me koi box ya ID mili tabhi process krenge
    first_result = detection_results[0]

    if first_result.boxes is not None and first_result.boxes.id is not None:

        # GPU memory (VRAM) se data CPU me copy kr rhe hain arrays me kaam karne ke liye
        all_boxes = first_result.boxes.xyxy.cpu().numpy()
        all_track_ids = first_result.boxes.id.int().cpu().tolist()
        all_classes = first_result.boxes.cls.int().cpu().tolist()
        all_confidences = first_result.boxes.conf.cpu().tolist()

        # Ek-ek krke saari detections check kr rhe hain
        for box, track_id, object_class, confidence in zip(
            all_boxes, all_track_ids, all_classes, all_confidences
        ):

            # Class 0 ka matlab 'Person' hota hai YOLO me. Hume sirf persons chahiye.
            if object_class == 0:
                person_count += 1

                detected_boxes.append(box)
                detected_track_ids.append(track_id)

                # Niche diye gaye helper functions call krke UI draw kr rhe hain
                draw_bounding_box(frame, box, track_id, confidence)

                center_x, center_y = calculate_center_point(box)
                draw_tracking_trail(frame, track_id, center_x, center_y)

    # Frame ke top-left corner pr total logo ki ginti likh rhe hain
    cv2.putText(
        frame,
        f"Unique Active People: {person_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
    )

    return frame, person_count, detected_boxes, detected_track_ids
