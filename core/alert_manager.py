import os
from datetime import datetime

import cv2

# Ensure the folder for saving alert images exists.
# exist_ok=True prevents an error if the folder is already there.
os.makedirs("static/alerts", exist_ok=True)


def save_intrusion_image(camera_frame):
    """
    Saves the provided camera frame as a JPEG image file to store evidence of an intrusion.

    Parameters:
        camera_frame (numpy.ndarray): A single image frame captured from the camera video stream.

    Returns:
        str: The file path where the image was saved.
    """

    # Get the current date and time to create a unique file name.
    # Format: YYYYMMDD_HHMMSS (e.g., 20260702_094044)
    current_time_string = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Combine the folder path, file prefix, and timestamp to create the full file path.
    evidence_image_path = f"static/alerts/intrusion_{current_time_string}.jpg"

    # Use OpenCV to save the image to the hard drive at the specified path.
    cv2.imwrite(evidence_image_path, camera_frame)

    # Return the path so other parts of the program (like the database) know where the file is.
    return evidence_image_path
