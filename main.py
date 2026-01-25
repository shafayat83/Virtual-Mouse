import cv2
import mediapipe as mp
import pyautogui
import time

# Initialize camera
cap = cv2.VideoCapture(0)

# Mediapipe hands
mp_hands = mp.solutions.hands
hand_detector = mp_hands.Hands(max_num_hands=1)
drawing_utils = mp.solutions.drawing_utils

# Screen size
screen_width, screen_height = pyautogui.size()

index_x, index_y = 0, 0

while True:
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape

    # Convert color
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = hand_detector.process(rgb_frame)
    hands = output.multi_hand_landmarks

    if hands:
        for hand in hands:
            drawing_utils.draw_landmarks(frame, hand)
            landmarks = hand.landmark
            for id, landmark in enumerate(landmarks):
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)

                if id == 8:  # Index finger tip
                    cv2.circle(frame, (x, y), 10, (0, 255, 255), cv2.FILLED)
                    index_x = screen_width / frame_width * x
                    index_y = screen_height / frame_height * y

                if id == 4:  # Thumb tip
                    cv2.circle(frame, (x, y), 10, (0, 255, 255), cv2.FILLED)
                    thumb_x = screen_width / frame_width * x
                    thumb_y = screen_height / frame_height * y

                    # Distance between thumb and index
                    distance = abs(index_y - thumb_y)

                    if distance < 20:
                        pyautogui.click()
                        time.sleep(0.3)
                    else:
                        pyautogui.moveTo(index_x, index_y, duration=0.01)

    cv2.imshow('Virtual Mouse', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
