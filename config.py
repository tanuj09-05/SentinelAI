"""
Sentinel AI Configuration File
All project settings are managed from here.
"""

# -------------------------------
# Camera Settings
# -------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# -------------------------------
# AI Model Settings
# -------------------------------
MODEL_PATH = "models/yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.5

# -------------------------------
# Database Settings
# -------------------------------
DATABASE_PATH = "database/sentinelai.db"

# -------------------------------
# Restricted Zone
# Format: (x1, y1, x2, y2)
# -------------------------------
RESTRICTED_ZONE = (100, 100, 500, 400)

# -------------------------------
# Alert Settings
# -------------------------------
SAVE_SCREENSHOT = True
SCREENSHOT_FOLDER = "screenshots"

# -------------------------------
# UI Settings
# -------------------------------
WINDOW_NAME = "Sentinel AI"
