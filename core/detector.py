from ultralytics import YOLO
import cv2

from config import MODEL_PATH

# Load YOLO model only once
model = YOLO(MODEL_PATH)


def detect(frame):
    """
    Detect people in a frame and draw bounding boxes.
    Returns:
        annotated_frame, person_count
    """

    results = model(frame)

    person_count = 0

    for box in results[0].boxes:

        class_id = int(box.cls[0])

        if class_id == 0:

            person_count += 1

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Person",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    cv2.putText(
        frame,
        f"People: {person_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    return frame, person_count, results[0].boxes