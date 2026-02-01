import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from collections import deque


class SeniorAIVirtualMouse:
    def __init__(self):
        # --- 1. System Config ---
        self.cam_w, self.cam_h = 640, 480
        self.screen_w, self.screen_h = pyautogui.size()

        # Hyper-parameters for smoothness
        self.smoothing_factor = 3  # Higher = smoother, but slightly more lag
        self.frame_margin = 120  # Box margin for easier screen reaching
        self.dead_zone = 2  # Ignore movements smaller than this (in pixels)

        # --- 2. Smoothing Buffers ---
        # History buffer for Weighted Moving Average (WMA)
        self.history_x = deque(maxlen=5)
        self.history_y = deque(maxlen=5)
        self.prev_x, self.prev_y = 0, 0

        # --- 3. MediaPipe Initialization ---
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,  # 1 for speed, 0 for max performance
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )
        self.mp_draw = mp.solutions.drawing_utils

        # --- 4. PyAutoGUI Optimization ---
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
        pyautogui.MINIMUM_DURATION = 0

        # State management
        self.is_dragging = False
        self.last_click_time = 0

    def smooth_coordinates(self, target_x, target_y):
        """Applies WMA and Dead-zone filtering for professional cursor feel."""
        self.history_x.append(target_x)
        self.history_y.append(target_y)

        # Calculate weighted average
        avg_x = sum(self.history_x) / len(self.history_x)
        avg_y = sum(self.history_y) / len(self.history_y)

        # Apply Dead-zone
        if abs(avg_x - self.prev_x) < self.dead_zone:
            avg_x = self.prev_x
        if abs(avg_y - self.prev_y) < self.dead_zone:
            avg_y = self.prev_y

        # Final Interpolation (EMA)
        final_x = self.prev_x + (avg_x - self.prev_x) / self.smoothing_factor
        final_y = self.prev_y + (avg_y - self.prev_y) / self.smoothing_factor

        self.prev_x, self.prev_y = final_x, final_y
        return final_x, final_y

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW for faster startup on Windows
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)
        cap.set(cv2.CAP_PROP_FPS, 60)  # Try to force 60fps

        p_time = 0

        while cap.isOpened():
            success, frame = cap.read()
            if not success: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            # Draw movement boundary (The "Active Zone")
            cv2.rectangle(frame, (self.frame_margin, self.frame_margin),
                          (self.cam_w - self.frame_margin, self.cam_h - self.frame_margin),
                          (255, 0, 255), 2)

            if results.multi_hand_landmarks:
                hand_lms = results.multi_hand_landmarks[0]
                self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)

                # Get specific landmarks
                # 4: Thumb Tip, 8: Index Tip, 12: Middle Tip, 16: Ring Tip
                lm = hand_lms.landmark
                ix, iy = int(lm[8].x * self.cam_w), int(lm[8].y * self.cam_h)
                tx, ty = int(lm[4].x * self.cam_w), int(lm[4].y * self.cam_h)
                mx, my = int(lm[12].x * self.cam_w), int(lm[12].y * self.cam_h)
                rx, ry = int(lm[16].x * self.cam_w), int(lm[16].y * self.cam_h)

                # --- GESTURE CALCULATIONS ---
                dist_thumb_index = np.hypot(ix - tx, iy - ty)
                dist_index_middle = np.hypot(mx - ix, my - iy)

                # Finger states (simple Y-axis check)
                index_up = lm[8].y < lm[6].y
                middle_up = lm[12].y < lm[10].y
                ring_up = lm[16].y < lm[14].y
                pinky_up = lm[20].y < lm[18].y

                # --- 1. MOVEMENT (Only Index Up) ---
                if index_up and not middle_up:
                    # Map range from camera box to screen
                    raw_x = np.interp(ix, (self.frame_margin, self.cam_w - self.frame_margin), (0, self.screen_w))
                    raw_y = np.interp(iy, (self.frame_margin, self.cam_h - self.frame_margin), (0, self.screen_h))

                    smooth_x, smooth_y = self.smooth_coordinates(raw_x, raw_y)
                    pyautogui.moveTo(smooth_x, smooth_y)
                    cv2.circle(frame, (ix, iy), 10, (0, 255, 0), cv2.FILLED)

                # --- 2. LEFT CLICK & DRAG (Index + Thumb) ---
                if dist_thumb_index < 30:
                    if not self.is_dragging:
                        pyautogui.mouseDown()
                        self.is_dragging = True
                    cv2.putText(frame, "HOLD/DRAG", (20, 50), 2, 0.8, (0, 255, 0), 2)
                else:
                    if self.is_dragging:
                        pyautogui.mouseUp()
                        self.is_dragging = False

                # --- 3. RIGHT CLICK (Index + Middle) ---
                if index_up and middle_up and dist_index_middle < 30:
                    curr_t = time.time()
                    if curr_t - self.last_click_time > 0.4:
                        pyautogui.rightClick()
                        self.last_click_time = curr_t
                    cv2.putText(frame, "RIGHT CLICK", (20, 50), 2, 0.8, (0, 0, 255), 2)

                # --- 4. SCROLL (Two Fingers Parallel) ---
                if index_up and middle_up and dist_index_middle > 40:
                    # Use middle finger movement for scrolling
                    scroll_speed = (iy - self.cam_h / 2) / 10
                    pyautogui.scroll(int(-scroll_speed))
                    cv2.putText(frame, "SCROLLING", (20, 50), 2, 0.8, (255, 255, 0), 2)

                # --- 5. COPY/PASTE (Three/Four Fingers) ---
                if index_up and middle_up and ring_up:
                    curr_t = time.time()
                    if curr_t - self.last_click_time > 1.0:
                        if pinky_up:
                            pyautogui.hotkey('ctrl', 'v')
                            print("PASTE")
                        else:
                            pyautogui.hotkey('ctrl', 'c')
                            print("COPY")
                        self.last_click_time = curr_t

            # FPS Counter
            c_time = time.time()
            fps = 1 / (c_time - p_time)
            p_time = c_time
            cv2.putText(frame, f"FPS: {int(fps)}", (self.cam_w - 120, 30), 1, 1.5, (0, 255, 0), 2)

            cv2.imshow("AI Smooth Mouse", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    mouse = SeniorAIVirtualMouse()
    mouse.run()
