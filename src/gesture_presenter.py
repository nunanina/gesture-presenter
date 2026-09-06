import time

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import win32con
import win32gui

# ============================================================
# Configuration
# ============================================================
CAMERA_INDEX = 0
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 320
CAMERA_FPS = 30

WINDOW_NAME = "Gesture Presenter"
WINDOW_WIDTH = 426
WINDOW_HEIGHT = 240
WINDOW_MARGIN_X = 10
WINDOW_MARGIN_Y = 40

MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.6
FACE_DETECTION_CONFIDENCE = 0.6
MAX_NUM_HANDS = 1
MODEL_COMPLEXITY = 0

CURSOR_X_RANGE = (0.60, 0.86)
CURSOR_Y_RANGE = (0.20, 0.40)
CURSOR_SMOOTHING_ALPHA = 0.3
CURSOR_MOVE_DURATION = 0.01

FRAME_DELAY = 1 / CAMERA_FPS
CLICK_COOLDOWN = 0.30
SLIDE_COOLDOWN = 1.00
START_PRESENTATION_COOLDOWN = 2.00
EXIT_COOLDOWN = 1.00

# Gesture patterns: [thumb, index, middle, ring, pinky]
GESTURE_CLICK = [0, 1, 0, 0, 0]
GESTURE_CURSOR = [0, 1, 1, 0, 0]
GESTURE_SLIDE = [0, 1, 1, 1, 0]
GESTURE_START_PRESENTATION = [0, 1, 1, 1, 1]
GESTURE_EXIT_PRESENTATION = [0, 1, 0, 0, 1]


class GesturePresenter:
    """Control presentation actions using hand gestures detected above the head."""

    def __init__(self) -> None:
        self.screen_width, self.screen_height = pyautogui.size()
        self.prev_cursor_x = 0
        self.prev_cursor_y = 0

        self.last_frame_time = 0.0
        self.next_click_time = 0.0
        self.next_slide_time = 0.0
        self.next_start_time = 0.0
        self.next_exit_time = 0.0

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_face = mp.solutions.face_detection

        self.hands = self.mp_hands.Hands(
            max_num_hands=MAX_NUM_HANDS,
            model_complexity=MODEL_COMPLEXITY,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        self.face_detector = self.mp_face.FaceDetection(
            min_detection_confidence=FACE_DETECTION_CONFIDENCE
        )

        self.capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.capture.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

        if not self.capture.isOpened():
            raise RuntimeError("Unable to open the camera.")

        self.window_x = self.screen_width - WINDOW_WIDTH - WINDOW_MARGIN_X
        self.window_y = self.screen_height - WINDOW_HEIGHT - WINDOW_MARGIN_Y
        self.first_show = True

    @staticmethod
    def get_fingers_status(hand_landmarks, hand_label: str) -> list[int]:
        """Return five binary values representing raised fingers."""
        fingers: list[int] = []

        thumb_tip = hand_landmarks.landmark[4]
        thumb_ip = hand_landmarks.landmark[3]

        if hand_label == "Right":
            fingers.append(1 if thumb_tip.x < thumb_ip.x else 0)
        else:
            fingers.append(1 if thumb_tip.x > thumb_ip.x else 0)

        finger_tips = (8, 12, 16, 20)
        finger_pips = (6, 10, 14, 18)

        for tip, pip in zip(finger_tips, finger_pips):
            is_raised = hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y
            fingers.append(1 if is_raised else 0)

        return fingers

    def get_cursor_position(self, hand_landmarks) -> tuple[int, int]:
        """Map index-finger coordinates to the screen with EMA smoothing."""
        norm_x = hand_landmarks.landmark[8].x
        norm_y = hand_landmarks.landmark[8].y

        target_x = np.interp(
            norm_x,
            CURSOR_X_RANGE,
            (0, self.screen_width),
        )
        target_y = np.interp(
            norm_y,
            CURSOR_Y_RANGE,
            (0, self.screen_height),
        )

        smoothed_x = int(
            self.prev_cursor_x * (1 - CURSOR_SMOOTHING_ALPHA)
            + target_x * CURSOR_SMOOTHING_ALPHA
        )
        smoothed_y = int(
            self.prev_cursor_y * (1 - CURSOR_SMOOTHING_ALPHA)
            + target_y * CURSOR_SMOOTHING_ALPHA
        )

        self.prev_cursor_x = smoothed_x
        self.prev_cursor_y = smoothed_y

        return smoothed_x, smoothed_y

    @staticmethod
    def get_face_top(face_result, frame):
        """Return normalized Y coordinate of the detected head top, if available."""
        if not face_result.detections:
            return None

        detection = face_result.detections[0]
        bbox = detection.location_data.relative_bounding_box
        face_top = bbox.ymin

        frame_height, frame_width, _ = frame.shape
        line_y = int(face_top * frame_height)
        cv2.line(frame, (0, line_y), (frame_width, line_y), (0, 255, 0), 2)

        return face_top

    def process_gesture(self, fingers: list[int], hand_label: str, hand_landmarks) -> None:
        """Map a recognized gesture to an operating-system command."""
        now = time.time()

        if fingers == GESTURE_CURSOR:
            x, y = self.get_cursor_position(hand_landmarks)
            pyautogui.moveTo(x, y, duration=CURSOR_MOVE_DURATION)
            return

        if fingers == GESTURE_CLICK and now >= self.next_click_time:
            pyautogui.click()
            self.next_click_time = now + CLICK_COOLDOWN
            return

        if fingers == GESTURE_SLIDE and now >= self.next_slide_time:
            if hand_label == "Right":
                pyautogui.press("right")
            elif hand_label == "Left":
                pyautogui.press("left")

            self.next_slide_time = now + SLIDE_COOLDOWN
            return

        if fingers == GESTURE_START_PRESENTATION and now >= self.next_start_time:
            pyautogui.hotkey("ctrl", "alt", "p")
            self.next_start_time = now + START_PRESENTATION_COOLDOWN
            return

        if fingers == GESTURE_EXIT_PRESENTATION and now >= self.next_exit_time:
            pyautogui.press("esc")
            self.next_exit_time = now + EXIT_COOLDOWN

    def configure_window(self) -> None:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, WINDOW_WIDTH, WINDOW_HEIGHT)
        cv2.moveWindow(WINDOW_NAME, self.window_x, self.window_y)

    def keep_window_on_top(self) -> None:
        hwnd = win32gui.FindWindow(None, WINDOW_NAME)
        if not hwnd:
            return

        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_STYLE,
            style & ~win32con.WS_OVERLAPPEDWINDOW,
        )
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            self.window_x,
            self.window_y,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            win32con.SWP_SHOWWINDOW,
        )

    def run(self) -> None:
        self.configure_window()

        try:
            while True:
                now = time.time()
                if now - self.last_frame_time < FRAME_DELAY:
                    time.sleep(0.001)
                    continue
                self.last_frame_time = now

                ret, frame = self.capture.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_result = self.face_detector.process(rgb)
                face_top = self.get_face_top(face_result, frame)

                hand_result = self.hands.process(rgb)
                if hand_result.multi_hand_landmarks:
                    for index, hand_landmarks in enumerate(hand_result.multi_hand_landmarks):
                        hand_label = (
                            hand_result.multi_handedness[index]
                            .classification[0]
                            .label
                        )

                        self.mp_draw.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                        )

                        index_tip_y = hand_landmarks.landmark[8].y
                        index_above_head = (
                            face_top is not None and index_tip_y < face_top
                        )

                        if not index_above_head:
                            continue

                        fingers = self.get_fingers_status(hand_landmarks, hand_label)
                        self.process_gesture(fingers, hand_label, hand_landmarks)

                cv2.imshow(WINDOW_NAME, frame)

                if self.first_show:
                    self.keep_window_on_top()
                    self.first_show = False

                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break

        finally:
            self.capture.release()
            self.hands.close()
            self.face_detector.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    presenter = GesturePresenter()
    presenter.run()
