"""
person_detection.py

This module is responsible only for detecting objects using YOLO.
It does NOT:
- Open the camera
- Display frames
- Handle keyboard input
- Save data
"""

from ultralytics import YOLO
from config import MODEL_PATH

# Load the YOLO model only once
model = YOLO(MODEL_PATH)


def detect(frame):
    """
    Detect objects in a single frame.

    Args:
        frame: Image frame from OpenCV.

    Returns:
        YOLO detection results.
    """
    results = model(frame)
    return results