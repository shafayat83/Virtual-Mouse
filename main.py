# hand_mouse_control.py

import cv2
import mediapipe as mp
import pyautogui
from pynput.keyboard import Controller
import time

# Screen size
screen_width, screen_height = pyautogui.size()

# Mediapipe hand detection setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Keyboard controller for copy/paste
keyboard = Controller()

# Webcam
cap = cv2.VideoCapture(0)

# Drag & Drop state
dragging = False

def distance(p1, p2):
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5

print("Hand Mouse Controller Started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)
    
    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        # Get landmarks
        index_tip = hand_landmarks.landmark[8]
        thumb_tip = hand_landmarks.landmark[4]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        # Move mouse with index finger
        x = int(index_tip.x * screen_width)
        y = int(index_tip.y * screen_height)
        pyautogui.moveTo(x, y)
        
        # LEFT CLICK: Thumb + Index close
        if distance(thumb_tip, index_tip) < 0.03:
            pyautogui.click()
            time.sleep(0.2)  # Prevent multiple clicks
        
        # RIGHT CLICK: Thumb + Middle finger close
        if distance(thumb_tip, middle_tip) < 0.03:
            pyautogui.click(button='right')
            time.sleep(0.2)
        
        # DRAG & DROP: Thumb + Index slightly apart
        if 0.03 < distance(thumb_tip, index_tip) < 0.06:
            if not dragging:
                pyautogui.mouseDown()
                dragging = True
        else:
            if dragging:
                pyautogui.mouseUp()
                dragging = False
        
        # SCROLL UP: Index + Middle fingers up
        if index_tip.y < thumb_tip.y and middle_tip.y < thumb_tip.y:
            pyautogui.scroll(40)
        
        # SCROLL DOWN: Ring + Pinky fingers up
        if ring_tip.y < thumb_tip.y and pinky_tip.y < thumb_tip.y:
            pyautogui.scroll(-40)
        
        # COPY: Thumb + Index + Middle together
        if distance(thumb_tip, index_tip) < 0.03 and distance(thumb_tip, middle_tip) < 0.03:
            with keyboard.pressed('ctrl'):
                keyboard.press('c')
                keyboard.release('c')
            time.sleep(0.5)
        
        # PASTE: Thumb + Ring + Pinky together
        if distance(thumb_tip, ring_tip) < 0.03 and distance(thumb_tip, pinky_tip) < 0.03:
            with keyboard.pressed('ctrl'):
                keyboard.press('v')
                keyboard.release('v')
            time.sleep(0.5)
    
    cv2.imshow("Hand Mouse Controller", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
