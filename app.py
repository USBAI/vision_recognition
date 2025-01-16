import sys
import cv2
import mediapipe as mp
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

# MediaPipe Pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils


class PushUpCounterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Push-Up Counter App")
        self.setGeometry(100, 100, 800, 600)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.pushup_count = 0
        self.last_angle = None
        self.direction = None  # 'up' or 'down'

        self.init_ui()

    def init_ui(self):
        # Layout setup
        self.label = QLabel(self)
        self.label.resize(800, 500)

        self.counter_label = QLabel("Push-Ups: 0", self)
        self.counter_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")

        # Layout placement
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.counter_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer.start(30)  # Start the timer for frame updates

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Flip the frame horizontally for natural mirroring
        frame = cv2.flip(frame, 1)

        # Process the frame with MediaPipe Pose
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb_frame)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks.landmark

            # Extract relevant joint coordinates
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            # Calculate the angle of the left elbow
            elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)

            # Push-up counting logic
            if elbow_angle > 160:  # When arms are fully extended
                self.direction = "up"
            elif elbow_angle < 90 and self.direction == "up":  # When arms are bent and going down
                self.direction = "down"
                self.pushup_count += 1
                self.counter_label.setText(f"Push-Ups: {self.pushup_count}")

            # Draw landmarks and connections on the frame
            mp_drawing.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Convert frame to QImage for display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(image))

    @staticmethod
    def calculate_angle(a, b, c):
        """
        Calculate the angle between three points: a (shoulder), b (elbow), and c (wrist).
        """
        a = np.array(a)  # Shoulder
        b = np.array(b)  # Elbow
        c = np.array(c)  # Wrist

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def closeEvent(self, event):
        self.cap.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PushUpCounterApp()
    window.show()
    sys.exit(app.exec_())
