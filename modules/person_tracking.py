from datetime import datetime
import os
import sqlite3

import cv2
from ultralytics import YOLO
from database.database import save_event
from core.alert_manager import save_intrusion_image
# Save one detected event into the SQLite database.
# This stores the event type, the time it happened, and the image path.



# Create the alerts folder if it does not already exist.
# This helps when the program needs to save alert images.
os.makedirs("alerts", exist_ok=True)

# Load the YOLO model once before starting the webcam loop.
# The model will be used to track people in each frame.
from config import MODEL_PATH

model = YOLO(MODEL_PATH)
# Open the default webcam.
# VideoCapture(0) means the first camera connected to the system.
video_capture = cv2.VideoCapture(0)

# These coordinates define the restricted zone.
# If the person's center point enters this area, we treat it as an intrusion.
from config import RESTRICTED_ZONE

zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE

# This flag prevents the same intrusion from being saved many times.
intrusion_active = False

while True:
    # Read one frame from the webcam.
    # success tells us whether the frame was captured correctly.
    # current_frame stores the image data.
    success, current_frame = video_capture.read()

    if not success:
        break

    # Run YOLO tracking on the current frame.
    # persist=True keeps tracking stable across frames.
    # classes=[0] means only the person class is detected.
    tracking_results = model.track(
        current_frame,
        persist=True,
        classes=[0]
    )

    # Draw the restricted zone on the frame.
    cv2.rectangle(
        current_frame,
        (zone_x1, zone_y1),
        (zone_x2, zone_y2),
        (0, 0, 255),
        3
    )

    # Add a label so the user knows what the red box means.
    cv2.putText(
        current_frame,
        "Restricted Zone",
        (zone_x1, zone_y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    person_inside_zone = False

    # Check whether YOLO found any boxes in this frame.
    if tracking_results[0].boxes is not None:
        # Process each detected person one by one.
        for detected_box in tracking_results[0].boxes:
            # Convert the box coordinates to integers for OpenCV drawing.
            x1, y1, x2, y2 = map(
                int,
                detected_box.xyxy[0]
            )

            # The tracking ID helps identify the same person across frames.
            track_id = "N/A"

            if detected_box.id is not None:
                track_id = int(detected_box.id[0])

            # Calculate the center point of the person.
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Draw a green bounding box around the person.
            cv2.rectangle(
                current_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Show the tracking ID above the box.
            cv2.putText(
                current_frame,
                f"ID: {track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Draw a small blue dot at the center of the person.
            cv2.circle(
                current_frame,
                (center_x, center_y),
                5,
                (255, 0, 0),
                -1
            )

            # Check if the person's center is inside the restricted zone.
            if (
                zone_x1 < center_x < zone_x2
                and
                zone_y1 < center_y < zone_y2
            ):
                person_inside_zone = True

    # Show the intrusion warning if a person enters the zone.
    if person_inside_zone:
        cv2.putText(
            current_frame,
            "INTRUSION DETECTED",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        # Save the screenshot only once while intrusion remains active.
        if not intrusion_active:
            intrusion_active = True

            filename = save_intrusion_image(current_frame)

            # Save the event in the database.
            save_event(
                "Intrusion",
                filename
            )

            print(f"[ALERT] Evidence Saved: {filename}")

    else:
        intrusion_active = False

    # Show the processed frame in a window.
    cv2.imshow(
        "SentinelAI Intrusion Detection",
        current_frame
    )

    # Press q to exit the program.
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the webcam when the loop ends.
video_capture.release()

# Close all OpenCV windows.
cv2.destroyAllWindows()