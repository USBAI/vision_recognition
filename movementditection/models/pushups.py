import mediapipe as mp
import cv2
import numpy as np
import base64

class PushupsModel:
    def __init__(self):
        # MediaPipe Pose setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.pushup_count = 0
        self.direction = None  # 'up' or 'down'

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

    def process_frame(self, frame_data):
        """
        Process the incoming frame data and calculate the push-up count.
        """
        try:
            # Decode the base64 frame
            img_data = base64.b64decode(frame_data)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                return {'error': 'Failed to decode frame'}

            # Process the frame with MediaPipe Pose
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.pose.process(rgb_frame)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks.landmark

                # Extract relevant joint coordinates
                left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                 landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                left_elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                              landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                left_wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                              landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                # Calculate the angle of the left elbow
                elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)

                # Push-up counting logic
                if elbow_angle > 160:  # Arms are extended
                    if self.direction == "down":
                        self.pushup_count += 1  # Count a push-up
                    self.direction = "up"
                elif elbow_angle < 90:  # Arms are bent
                    self.direction = "down"

            return {'count': self.pushup_count}

        except Exception as e:
            return {'error': str(e)}
