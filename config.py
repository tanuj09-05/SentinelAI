"""
Sentinel AI Configuration File
"""

CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

MODEL_PATH = "models/yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.5

DATABASE_PATH = "database/sentinelai.db"

# Format: (x1, y1, x2, y2)
RESTRICTED_ZONE = (100, 100, 500, 400)

SAVE_SCREENSHOT = True
SCREENSHOT_FOLDER = "screenshots"

WINDOW_NAME = "Sentinel AI"
