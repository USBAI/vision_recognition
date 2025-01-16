from flask import Flask, request, jsonify
from flask_cors import CORS
import mediapipe as mp
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app)

# MediaPipe Pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Global variables for push-up counting
pushup_count = 0
direction = None  # 'up' or 'down'


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


@app.route('/api/pushup_count', methods=['POST'])
def pushup_count_endpoint():
    global pushup_count, direction

    try:
        data = request.json
        frame_data = data.get('frame')
        if not frame_data:
            return jsonify({'error': 'No frame provided'}), 400

        # Decode the base64 frame
        img_data = base64.b64decode(frame_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'error': 'Failed to decode frame'}), 400

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
            elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

            # Push-up counting logic
            if elbow_angle > 160:  # Arms are extended
                if direction == "down":
                    pushup_count += 1  # Count a push-up
                direction = "up"
            elif elbow_angle < 90:  # Arms are bent
                direction = "down"

        return jsonify({'count': pushup_count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return "Push-Up Counting API is running!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
