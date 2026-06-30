import cv2
from config import CAMERA_INDEX


class Camera:

    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            raise Exception("Could not open camera.")

    def read(self):
        success, frame = self.cap.read()
        return success, frame

    def release(self):
        self.cap.release()