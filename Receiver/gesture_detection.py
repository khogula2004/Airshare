import cv2
import mediapipe as mp
import time

class GestureDetector:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.prev_y = None
        self.prev_time = time.time()

        self.last_gesture = None
        self.cooldown_start = 0
        self.cooldown_period = 1.0  # in seconds

    def is_fist(self, landmarks):
        tips = [8, 12, 16, 20]
        folded = sum(1 for tip in tips if landmarks[tip].y > landmarks[tip - 2].y)
        return folded >= 3  # More strict than before

    def is_hand_open(self, landmarks):
        tips = [8, 12, 16, 20]
        extended = sum(1 for tip in tips if landmarks[tip].y < landmarks[tip - 2].y)
        return extended >= 3

    def detect(self, frame):
        gesture = None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        now = time.time()

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                lm = hand.landmark
                self.mp_draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)

                wrist_y = lm[0].y

                # === GRAB ===
                if self.is_fist(lm) and self.last_gesture != "grab":
                    gesture = "grab"
                    self.last_gesture = "grab"
                    self.cooldown_start = now
                    self.prev_y = wrist_y
                    self.prev_time = now

                # === THROW ===
                elif self.is_hand_open(lm) and self.last_gesture == "grab":
                    if self.prev_y is not None:
                        velocity = (self.prev_y - wrist_y) / (now - self.prev_time + 1e-5)
                        if velocity > 0.6 and (now - self.cooldown_start) > self.cooldown_period:
                            gesture = "throw"
                            self.last_gesture = "throw"
                            self.cooldown_start = now
                    self.prev_y = wrist_y
                    self.prev_time = now

        return frame, gesture
