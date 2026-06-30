from ultralytics import YOLO
import cv2

# Load the YOLO model once before starting the webcam loop.
# YOLO will use this model to detect objects in each video frame.
model = YOLO("yolov8n.pt")

# Open the default webcam.
# VideoCapture(0) means we want to read frames from the first camera device.
video_capture = cv2.VideoCapture(0)

while True:
    # Read one frame from the webcam.
    # ret tells us whether the frame was read successfully.
    # frame contains the actual image data.
    success, current_frame = video_capture.read()

    if not success:
        break

    # Run object detection on the current frame.
    # The model returns all detected objects in this image.
    detection_results = model(current_frame)

    # Keep track of how many people are detected in this frame.
    person_count = 0

    # results[0] contains the detections for the current frame.
    # boxes gives us each detected object bounding box one by one.
    for detected_box in detection_results[0].boxes:

        # box.cls stores the class id predicted by YOLO.
        # Class id 0 means "person" in the COCO dataset used by YOLO.
        class_id = int(detected_box.cls[0])

        if class_id == 0:
            person_count += 1

            # Convert the floating-point box coordinates into integers.
            # We need integer values because OpenCV drawing functions expect them.
            x1, y1, x2, y2 = map(int, detected_box.xyxy[0])

            # Draw a green rectangle around the detected person.
            cv2.rectangle(
                current_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Write the label "Person" above the rectangle.
            cv2.putText(
                current_frame,
                "Person",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    # Show the total number of people detected in the current frame.
    cv2.putText(
        current_frame,
        f"People Count: {person_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        3
    )

    # Display the processed frame in a window.
    cv2.imshow("SentinelAI Counter", current_frame)

    # Wait for 1 millisecond and check whether the user pressed the q key.
    # If q is pressed, stop the loop and close the program.
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the webcam when we are done.
video_capture.release()

# Close all OpenCV windows.
cv2.destroyAllWindows()