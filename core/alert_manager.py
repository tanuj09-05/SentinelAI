import os
from datetime import datetime

import cv2

os.makedirs("static/alerts", exist_ok=True)

def save_intrusion_image(camera_frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"static/alerts/intrusion_{timestamp}.jpg"
    
    cv2.imwrite(filepath, camera_frame)
    return filepath
