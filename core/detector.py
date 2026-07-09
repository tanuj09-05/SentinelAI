import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
from config import MODEL_PATH

try:
    yolo_model = YOLO(MODEL_PATH)
    AI_STATUS = "online"
except Exception as error:
    print(f"[ERROR] YOLO model load nhi ho paya: {error}")
    yolo_model = None
    AI_STATUS = "offline"

def get_ai_status():
    return AI_STATUS

movement_history = defaultdict(list)

def draw_bounding_box(frame, box, track_id, confidence):
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    label = f"ID:{track_id} {confidence:.2f}"
    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

def calculate_center_point(box):
    x1, y1, x2, y2 = map(int, box)
    return (x1 + x2) // 2, (y1 + y2) // 2

def draw_tracking_trail(frame, track_id, center_x, center_y):
    cv2.circle(frame, (center_x, center_y), 4, (0, 0, 255), -1)
    
    person_path = movement_history[track_id]
    person_path.append((center_x, center_y))
    
    if len(person_path) > 20:
        person_path.pop(0)
        
    if len(person_path) > 1:
        points_array = np.array(person_path, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [points_array], isClosed=False, color=(0, 255, 255), thickness=2)

def detect(frame):
    if yolo_model is None:
        return frame, 0, [], []

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

    first_result = detection_results[0]

    if first_result.boxes is not None and first_result.boxes.id is not None:
        all_boxes = first_result.boxes.xyxy.cpu().numpy()
        all_track_ids = first_result.boxes.id.int().cpu().tolist()
        all_classes = first_result.boxes.cls.int().cpu().tolist()
        all_confidences = first_result.boxes.conf.cpu().tolist()

        for box, track_id, object_class, confidence in zip(all_boxes, all_track_ids, all_classes, all_confidences):
            if object_class == 0:
                person_count += 1
                detected_boxes.append(box)
                detected_track_ids.append(track_id)

                draw_bounding_box(frame, box, track_id, confidence)
                center_x, center_y = calculate_center_point(box)
                draw_tracking_trail(frame, track_id, center_x, center_y)

    cv2.putText(frame, f"Unique Active People: {person_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return frame, person_count, detected_boxes, detected_track_ids
