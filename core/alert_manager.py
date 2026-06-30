import os
import cv2
from datetime import datetime

# Create alert folder if it doesn't exist
os.makedirs("static/alerts", exist_ok=True)


def save_intrusion_image(frame):
    """
    Save intrusion evidence image and return its path.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"static/alerts/intrusion_{timestamp}.jpg"

    cv2.imwrite(filename, frame)

    return filename