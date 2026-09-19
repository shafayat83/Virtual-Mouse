"""
================================================================================
⚡ CYBER//LINK v2077 - DIRECTIONAL & FLAT-HAND VIRTUAL AIR MOUSE (ALL-IN-ONE)
================================================================================
A production-ready Virtual Air Mouse with gesture-driven control:
1. Cursor Movement     : Smoothly tracks index finger tip with adaptive One-Euro smoothing.
2. Left Click          : Standard left-click triggered by Thumb + Index pinch touch.
3. Right Click         : Index finger points sharply to the RIGHT relative to hand.
4. Left-Side Action    : Index finger points sharply to the LEFT (Middle-Click / Secondary).
5. Up / Down Actions   : Index finger points directly UPWARD or directly DOWNWARD.
6. Flat Hand Scrolling : Hand held in a flat hand sign (all fingers extended together)
                         maps hand movement and tilt to scroll delta.

Dependencies:
    pip install opencv-python mediapipe pyautogui numpy pygame

Interactive Controls (Hotkeys):
  * [SPACE]      : Freeze / Pause Cursor Tracking
  * [<] / [>]    : Decrease / Increase Pointer Sensitivity
  * [-] / [+]    : Decrease / Increase Smoothness Factor
  * [[] / []]    : Expand / Shrink Active Interaction Matrix
  * [P]          : Cycle Pinch Sensitivity (Firm / Normal / Sensitive)
  * [S]          : Toggle AI Smoothing (Adaptive One-Euro vs Raw)
  * [M]          : Toggle Cyber Audio Cues
  * [C]          : Toggle CRT Scanlines
  * [R]          : Recalibrate Camera Sensors
  * [Q] or [ESC] : Disconnect / Exit
================================================================================
"""

import os
import sys
import time
import math
import threading
import urllib.request
from collections import deque

import cv2
import numpy as np
import pyautogui
import mediapipe as mp

# PyAutoGUI optimization for responsive real-time control
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False
pyautogui.MINIMUM_DURATION = 0.0

# ------------------------------------------------------------------------------
# 1. Synthesized Sci-Fi Audio Engine (Zero External Audio Files)
# ------------------------------------------------------------------------------
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except Exception:
    HAS_PYGAME = False

try:
    import winsound
    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False


class CyberAudio:
    """Zero-file synthesized sci-fi sound effects engine."""
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        if HAS_PYGAME:
            self._synthesize_all()

    def _make_tone(self, freq=1000, duration=0.08, wave_type="sine", decay=3.0, vol=0.35):
        try:
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            if wave_type == "sine":
                tone = np.sin(2 * np.pi * freq * t)
            elif wave_type == "square":
                tone = np.sign(np.sin(2 * np.pi * freq * t))
            elif wave_type == "sweep_up":
                f = np.linspace(freq, freq * 1.8, len(t))
                tone = np.sin(2 * np.pi * f * t)
            elif wave_type == "sweep_down":
                f = np.linspace(freq * 1.5, freq * 0.7, len(t))
                tone = np.sin(2 * np.pi * f * t)
            elif wave_type == "chord":
                tone = (
                    np.sin(2 * np.pi * freq * t) +
                    np.sin(2 * np.pi * (freq * 1.25) * t) +
                    np.sin(2 * np.pi * (freq * 1.5) * t)
                ) / 3.0
            else:
                tone = np.sin(2 * np.pi * freq * t)

            env = np.exp(-decay * np.linspace(0, 1, len(t)))
            mono = (tone * env * 32767 * vol).astype(np.int16)
            stereo = np.column_stack((mono, mono))
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def _synthesize_all(self):
        try:
            self.sounds["click"] = self._make_tone(1900, 0.035, "sweep_down", 4.0, 0.4)
            self.sounds["double_click"] = self._make_tone(2200, 0.04, "sweep_up", 3.0, 0.4)
            self.sounds["right_click"] = self._make_tone(950, 0.05, "sweep_up", 3.0, 0.4)
            self.sounds["left_action"] = self._make_tone(1150, 0.05, "sweep_down", 3.0, 0.35)
            self.sounds["up_action"] = self._make_tone(2400, 0.04, "sweep_up", 3.0, 0.35)
            self.sounds["down_action"] = self._make_tone(700, 0.06, "sweep_down", 2.5, 0.35)
            self.sounds["lock"] = self._make_tone(1400, 0.06, "sweep_up", 2.0, 0.35)
            self.sounds["unlock"] = self._make_tone(900, 0.05, "sweep_down", 2.5, 0.35)
            self.sounds["scroll"] = self._make_tone(1600, 0.015, "sine", 5.0, 0.22)
            self.sounds["toggle"] = self._make_tone(1200, 0.04, "sweep_up", 3.0, 0.3)
            self.sounds["start"] = self._make_tone(523, 0.22, "chord", 1.8, 0.45)
            self.sounds["error"] = self._make_tone(140, 0.09, "square", 2.0, 0.3)
        except Exception:
            pass

    def play(self, sound_name):
        if not self.enabled:
            return

        if HAS_PYGAME and sound_name in self.sounds and self.sounds[sound_name] is not None:
            try:
                self.sounds[sound_name].play()
                return
            except Exception:
                pass

        if HAS_WINSOUND:
            freq_map = {
                "click": 1800, "double_click": 2100, "right_click": 1100, "left_action": 1300,
                "up_action": 2000, "down_action": 800, "lock": 1500, "unlock": 900,
                "scroll": 1700, "toggle": 1200, "start": 1000, "error": 250
            }
            freq = freq_map.get(sound_name, 1200)

            def beep():
                try:
                    winsound.Beep(freq, 25)
                except Exception:
                    pass

            threading.Thread(target=beep, daemon=True).start()

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.play("toggle")
        return self.enabled


# ------------------------------------------------------------------------------
# 2. Adaptive Speed-Scaled One-Euro Filter (Ultra-Smooth Cursor Movement)
# ------------------------------------------------------------------------------
class AdaptiveSpeedSmoother:
    """
    Velocity-scaled One-Euro filter:
    High damping at low speeds = zero subpixel jitter or hand tremor.
    Low damping at high speeds = snappy, instantaneous cursor response.
    """
    def __init__(self, min_factor=1.8, max_factor=8.5, speed_threshold=28.0, dead_zone=2.0):
        self.prev_x = None
        self.prev_y = None
        self.min_factor = min_factor
        self.max_factor = max_factor
        self.speed_threshold = speed_threshold
        self.dead_zone = dead_zone
        self.user_smoothness = 5.0

    def set_user_smoothness(self, val):
        self.user_smoothness = max(1.0, min(10.0, float(val)))
        self.max_factor = 3.0 + (self.user_smoothness / 10.0) * 8.0
        self.min_factor = 1.2 + (self.user_smoothness / 10.0) * 1.5

    def filter(self, target_x, target_y, enabled=True):
        if self.prev_x is None:
            self.prev_x, self.prev_y = target_x, target_y
            return target_x, target_y

        if not enabled:
            self.prev_x, self.prev_y = target_x, target_y
            return target_x, target_y

        dx = target_x - self.prev_x
        dy = target_y - self.prev_y
        dist = math.hypot(dx, dy)

        if dist < self.dead_zone:
            return self.prev_x, self.prev_y

        velocity_ratio = min(1.0, dist / max(1.0, self.speed_threshold))
        dynamic_factor = self.max_factor - velocity_ratio * (self.max_factor - self.min_factor)

        curr_x = self.prev_x + dx / dynamic_factor
        curr_y = self.prev_y + dy / dynamic_factor

        self.prev_x, self.prev_y = curr_x, curr_y
        return curr_x, curr_y


# ------------------------------------------------------------------------------
# 3. Cyberpunk HUD Graphics Engine
# ------------------------------------------------------------------------------
class CyberHUD:
    """Renders Cyberpunk HUD elements, reticles, skeletons, telemetry, and directional markers."""
    CYAN = (255, 243, 0)       # #00f3ff
    MAGENTA = (85, 0, 255)      # #ff0055
    YELLOW = (0, 234, 255)      # #ffea00
    GREEN = (102, 255, 0)      # #00ff66
    RED = (30, 40, 255)        # Warning red
    WHITE = (255, 255, 255)
    DARK_BG = (17, 13, 13)     # #0d0d11
    GRID_COLOR = (45, 38, 55)

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # Index
        (9, 10), (10, 11), (11, 12),           # Middle
        (13, 14), (14, 15), (15, 16),          # Ring
        (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
        (5, 9), (9, 13), (13, 17)              # Palm knuckles
    ]

    def __init__(self):
        self.rotation_angle = 0
        self.shockwaves = []
        self.show_scanlines = True

    def update_animation(self):
        self.rotation_angle = (self.rotation_angle + 6) % 360

    def add_shockwave(self, x, y, color=None, max_radius=42):
        if color is None:
            color = self.CYAN
        self.shockwaves.append({
            "x": int(x), "y": int(y),
            "radius": 8, "max_radius": max_radius,
            "color": color, "speed": 4
        })

    def draw_shockwaves(self, frame):
        active = []
        for sw in self.shockwaves:
            sw["radius"] += sw["speed"]
            if sw["radius"] < sw["max_radius"]:
                alpha = 1.0 - (sw["radius"] / sw["max_radius"])
                thickness = max(1, int(3 * alpha))
                cv2.circle(frame, (sw["x"], sw["y"]), int(sw["radius"]), sw["color"], thickness, cv2.LINE_AA)
                active.append(sw)
        self.shockwaves = active

    def draw_hud_header(self, frame, fps, mode_text="IDLE", sound_on=True, smoothing_on=True, is_frozen=False):
        w = frame.shape[1]
        header_poly = np.array([
            [15, 6], [w - 15, 6], [w - 30, 48],
            [w * 2 // 3, 48], [w * 2 // 3 - 12, 38],
            [w // 3 + 12, 38], [w // 3, 48], [30, 48]
        ], np.int32)

        overlay = frame.copy()
        cv2.fillPoly(overlay, [header_poly], self.DARK_BG)
        cv2.polylines(overlay, [header_poly], True, self.CYAN, 1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "CYBER//LINK", (36, 28), cv2.FONT_HERSHEY_DUPLEX, 0.65, self.CYAN, 2, cv2.LINE_AA)
        cv2.putText(frame, "AIR MOUSE v2077", (174, 27), cv2.FONT_HERSHEY_PLAIN, 0.85, self.YELLOW, 1, cv2.LINE_AA)

        # Center Status Badge
        display_status = "[FROZEN]" if is_frozen else f">> {mode_text} <<"
        status_col = self.RED if is_frozen else self.WHITE
        cv2.putText(frame, display_status, (w // 3 + 15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.46, status_col, 1, cv2.LINE_AA)

        # Indicators
        snd_label = "SND:ON" if sound_on else "SND:OFF"
        cv2.putText(frame, snd_label, (w - 235, 30), cv2.FONT_HERSHEY_PLAIN, 0.82, self.GREEN if sound_on else (100, 100, 100), 1, cv2.LINE_AA)

        sm_label = "SMOOTH" if smoothing_on else "RAW"
        cv2.putText(frame, sm_label, (w - 165, 30), cv2.FONT_HERSHEY_PLAIN, 0.82, self.CYAN if smoothing_on else (100, 100, 100), 1, cv2.LINE_AA)

        fps_color = self.GREEN if fps >= 45 else (self.YELLOW if fps >= 25 else self.RED)
        cv2.putText(frame, f"FPS:{int(fps):02d}", (w - 75, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, fps_color, 1, cv2.LINE_AA)

    def draw_active_matrix(self, frame, margin_x, margin_y, cam_w, cam_h):
        x1, y1 = margin_x, margin_y
        x2, y2 = cam_w - margin_x, cam_h - margin_y
        corner_len = 26

        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), self.GRID_COLOR, 1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Tactical Corner Brackets
        for cx, cy, dx, dy in [(x1, y1, corner_len, corner_len), (x2, y1, -corner_len, corner_len),
                               (x1, y2, corner_len, -corner_len), (x2, y2, -corner_len, -corner_len)]:
            cv2.line(frame, (cx, cy), (cx + dx, cy), self.YELLOW, 2, cv2.LINE_AA)
            cv2.line(frame, (cx, cy), (cx, cy + dy), self.YELLOW, 2, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 3, self.CYAN, cv2.FILLED)

        cv2.putText(frame, "ACTIVE SENSOR MATRIX", (x1 + 6, y1 - 8), cv2.FONT_HERSHEY_PLAIN, 0.8, self.YELLOW, 1, cv2.LINE_AA)
        cv2.putText(frame, f"FOV: {cam_w - 2*margin_x}x{cam_h - 2*margin_y}", (x2 - 110, y2 + 16), cv2.FONT_HERSHEY_PLAIN, 0.75, self.CYAN, 1, cv2.LINE_AA)

    def draw_cyber_hand(self, frame, landmarks, cam_w, cam_h):
        raw_list = getattr(landmarks, "landmark", landmarks)
        coords = {}
        for idx, lm in enumerate(raw_list):
            coords[idx] = (int(lm.x * cam_w), int(lm.y * cam_h))

        # Neon Glow Bone Filaments
        for p1_idx, p2_idx in self.HAND_CONNECTIONS:
            pt1 = coords[p1_idx]
            pt2 = coords[p2_idx]
            cv2.line(frame, pt1, pt2, self.MAGENTA, 4, cv2.LINE_AA)
            cv2.line(frame, pt1, pt2, self.CYAN, 1, cv2.LINE_AA)

        # Tech Joint Nodes
        for idx, pt in coords.items():
            if idx in [4, 8, 12, 16, 20]:
                cv2.circle(frame, pt, 6, self.CYAN, 1, cv2.LINE_AA)
                cv2.circle(frame, pt, 3, self.WHITE, cv2.FILLED)
            elif idx == 0:
                cv2.circle(frame, pt, 7, self.YELLOW, 2, cv2.LINE_AA)
                cv2.circle(frame, pt, 3, self.YELLOW, cv2.FILLED)
            else:
                cv2.circle(frame, pt, 3, self.MAGENTA, cv2.FILLED)
                cv2.circle(frame, pt, 5, self.CYAN, 1, cv2.LINE_AA)
        return coords

    def draw_targeting_reticle(self, frame, x, y, dir_mode="AIM_MOVE"):
        rad = 18
        if dir_mode == "RIGHT_CLICK":
            col = self.MAGENTA
            tag = "▶ RIGHT CLICK"
        elif dir_mode == "LEFT_ACTION":
            col = self.CYAN
            tag = "◀ LEFT ACTION"
        elif dir_mode == "UP_ACTION":
            col = self.GREEN
            tag = "▲ UP ACTION"
        elif dir_mode == "DOWN_ACTION":
            col = self.YELLOW
            tag = "▼ DOWN ACTION"
        else:
            col = self.CYAN
            tag = f"AIM:{x:03d},{y:03d}"

        # Rotating outer brackets
        for deg in [0, 90, 180, 270]:
            cur_deg = math.radians(deg + self.rotation_angle)
            p1_x = int(x + rad * math.cos(cur_deg))
            p1_y = int(y + rad * math.sin(cur_deg))
            p2_x = int(x + (rad + 6) * math.cos(cur_deg))
            p2_y = int(y + (rad + 6) * math.sin(cur_deg))
            cv2.line(frame, (p1_x, p1_y), (p2_x, p2_y), col, 2, cv2.LINE_AA)

        cv2.circle(frame, (x, y), rad - 4, col, 1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 2, self.WHITE, cv2.FILLED)
        cv2.putText(frame, tag, (x + 22, y - 8), cv2.FONT_HERSHEY_PLAIN, 0.8, col, 1, cv2.LINE_AA)

    def draw_distance_beam(self, frame, p1, p2, dist, threshold_px):
        is_locked = dist < threshold_px
        col = self.GREEN if is_locked else (self.YELLOW if dist < threshold_px * 1.6 else self.CYAN)
        cv2.line(frame, p1, p2, col, 2, cv2.LINE_AA)

        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        tag = f"PINCH:{int(dist)}px [{'LOCK' if is_locked else 'FREE'}]"
        cv2.rectangle(frame, (mid_x - 4, mid_y - 12), (mid_x + 105, mid_y + 4), self.DARK_BG, cv2.FILLED)
        cv2.putText(frame, tag, (mid_x, mid_y), cv2.FONT_HERSHEY_PLAIN, 0.75, col, 1, cv2.LINE_AA)

    def draw_telemetry_panel(self, frame, cur_x, cur_y, screen_w, screen_h, gesture_name, is_dragging,
                             sensitivity, smoothness, is_frozen):
        h, w = frame.shape[:2]
        panel_x = 16
        panel_y = h - 138
        panel_w = 225
        panel_h = 124

        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), self.DARK_BG, cv2.FILLED)
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), self.CYAN, 1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        cv2.putText(frame, "// NEURAL TELEMETRY //", (panel_x + 8, panel_y + 16), cv2.FONT_HERSHEY_PLAIN, 0.82, self.CYAN, 1, cv2.LINE_AA)
        cv2.putText(frame, f"CURSOR: {int(cur_x)}, {int(cur_y)}", (panel_x + 8, panel_y + 34), cv2.FONT_HERSHEY_PLAIN, 0.8, self.WHITE, 1, cv2.LINE_AA)

        state_str = "PAUSED [SPACE]" if is_frozen else ("DRAG-LOCK" if is_dragging else gesture_name)
        status_col = self.RED if is_frozen else (self.GREEN if is_dragging else (self.YELLOW if gesture_name != "IDLE" else (160, 160, 160)))
        cv2.putText(frame, f"ACTION: {state_str}", (panel_x + 8, panel_y + 52), cv2.FONT_HERSHEY_PLAIN, 0.82, status_col, 1, cv2.LINE_AA)

        cv2.putText(frame, f"SENS: {sensitivity:.1f}x [</>]", (panel_x + 8, panel_y + 70), cv2.FONT_HERSHEY_PLAIN, 0.8, self.YELLOW, 1, cv2.LINE_AA)
        cv2.putText(frame, f"SMOOTH: {int(smoothness)}/10 [-/+]", (panel_x + 8, panel_y + 88), cv2.FONT_HERSHEY_PLAIN, 0.8, self.CYAN, 1, cv2.LINE_AA)
        cv2.putText(frame, "[SPACE]FREEZE [Q]QUIT", (panel_x + 8, panel_y + 106), cv2.FONT_HERSHEY_PLAIN, 0.72, (200, 200, 200), 1, cv2.LINE_AA)

    def draw_action_badge(self, frame, text, color=None):
        if color is None:
            color = self.CYAN
        h, w = frame.shape[:2]
        bx, by = w // 2 - 130, 62
        bw, bh = 260, 32
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (22, 16, 28), cv2.FILLED)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), color, 2, cv2.LINE_AA)
        cv2.putText(frame, f">> {text} <<", (bx + 14, by + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, 2, cv2.LINE_AA)

    def apply_scanlines(self, frame):
        if self.show_scanlines:
            frame[0::3, :] = (frame[0::3, :] * 0.86).astype(np.uint8)


# ------------------------------------------------------------------------------
# 4. Universal Hand Tracking Detector (MediaPipe 1.0+ Tasks with Auto-Download)
# ------------------------------------------------------------------------------
class UniversalHandDetector:
    def __init__(self):
        self.mode = "tasks"
        self.detector = None
        self.solutions_hands = None

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            self.mode = "solutions"
            self.solutions_hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                model_complexity=1,
                min_detection_confidence=0.45,  # High sensitivity = instant lock & zero dropped hands
                min_tracking_confidence=0.45
            )
            print("[CYBER//LINK] Hand Engine: Solutions API (High Sensitivity)")
        else:
            self.mode = "tasks"
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "hand_landmarker.task")
            if not os.path.exists(model_path):
                print("[CYBER//LINK] Downloading neural model asset (hand_landmarker.task)...")
                model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
                urllib.request.urlretrieve(model_url, model_path)
                print("[CYBER//LINK] Model download completed.")

            base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                min_hand_detection_confidence=0.45,
                min_hand_presence_confidence=0.45,
                min_tracking_confidence=0.45,
                running_mode=mp.tasks.vision.RunningMode.IMAGE
            )
            self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
            print("[CYBER//LINK] Hand Engine: Tasks API (High Sensitivity: 0.45)")

    def find_hand(self, frame_bgr):
        try:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            if self.mode == "solutions":
                res = self.solutions_hands.process(rgb)
                return res.multi_hand_landmarks[0] if res.multi_hand_landmarks else None
            else:
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                res = self.detector.detect(mp_img)
                return res.hand_landmarks[0] if res.hand_landmarks else None
        except Exception:
            return None


# ------------------------------------------------------------------------------
# 5. Rotation-Invariant Finger Extension & Gesture Classifier
# ------------------------------------------------------------------------------
def evaluate_finger_extensions(coords):
    """
    Computes finger extensions using 3D-aware radial vectors relative to the
    wrist and knuckles. Completely invariant to hand rotation and tilt!
    """
    wrist = np.array(coords[0], dtype=float)

    def is_finger_extended(tip_id, pip_id, mcp_id):
        tip = np.array(coords[tip_id], dtype=float)
        pip = np.array(coords[pip_id], dtype=float)
        mcp = np.array(coords[mcp_id], dtype=float)
        d_tip = np.linalg.norm(tip - wrist)
        d_pip = np.linalg.norm(pip - wrist)
        d_mcp = np.linalg.norm(mcp - wrist)
        return (d_tip > d_pip * 1.10) and (d_tip > d_mcp * 1.25)

    index_up = is_finger_extended(8, 6, 5)
    middle_up = is_finger_extended(12, 10, 9)
    ring_up = is_finger_extended(16, 14, 13)
    pinky_up = is_finger_extended(20, 18, 17)

    # Thumb check
    thumb_tip = np.array(coords[4], dtype=float)
    thumb_ip = np.array(coords[3], dtype=float)
    pinky_mcp = np.array(coords[17], dtype=float)
    thumb_up = np.linalg.norm(thumb_tip - pinky_mcp) > (np.linalg.norm(thumb_ip - pinky_mcp) * 1.12)

    return thumb_up, index_up, middle_up, ring_up, pinky_up


def classify_index_pointing_direction(coords):
    """
    Calculates index finger orientation relative to the hand orientation axis.
    Returns: (direction_type, relative_angle_deg, screen_angle_deg)
      - RIGHT_CLICK: Index points sharply to the right side relative to hand (45° <= rel <= 135°)
      - LEFT_ACTION: Index points sharply to the left side relative to hand (-135° <= rel <= -45°)
      - UP_ACTION  : Index points directly upward (-115° <= screen <= -65°)
      - DOWN_ACTION: Index points directly downward (abs(rel) >= 140° or 65° <= screen <= 115°)
      - AIM_MOVE   : Normal forward in-line index aiming for smooth cursor movement
    """
    wrist = coords[0]
    mcp_index = coords[5]
    tip_index = coords[8]

    hw_x = mcp_index[0] - wrist[0]
    hw_y = mcp_index[1] - wrist[1]
    hand_angle = math.atan2(hw_y, hw_x)

    f_x = tip_index[0] - mcp_index[0]
    f_y = tip_index[1] - mcp_index[1]
    finger_angle = math.atan2(f_y, f_x)

    rel_angle = math.degrees(finger_angle - hand_angle)
    while rel_angle > 180:
        rel_angle -= 360
    while rel_angle < -180:
        rel_angle += 360

    screen_angle = math.degrees(finger_angle)

    # 1. Sharply Right relative to hand (Right Click)
    if 45 <= rel_angle <= 135:
        # Check if hand is held sideways and index points straight UP
        if -115 <= screen_angle <= -65:
            return "UP_ACTION", rel_angle, screen_angle
        return "RIGHT_CLICK", rel_angle, screen_angle

    # 2. Sharply Left relative to hand (Left-Side Action / Secondary Click)
    elif -135 <= rel_angle <= -45:
        if -115 <= screen_angle <= -65:
            return "UP_ACTION", rel_angle, screen_angle
        return "LEFT_ACTION", rel_angle, screen_angle

    # 3. Directly Downward
    elif abs(rel_angle) >= 140 or (65 <= screen_angle <= 115 and rel_angle > 35):
        return "DOWN_ACTION", rel_angle, screen_angle

    # 4. Standard in-line aiming (Smooth Cursor Movement)
    else:
        return "AIM_MOVE", rel_angle, screen_angle


# ------------------------------------------------------------------------------
# 6. Optical Sensor Auto-Discovery
# ------------------------------------------------------------------------------
def find_working_camera(cam_w=640, cam_h=480):
    """Auto-scans camera devices across indices and backends."""
    print("[CYBER//LINK] Scanning optical sensors...")
    for idx in [0, 1, 2, 3]:
        for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)
                        cap.set(cv2.CAP_PROP_FPS, 60)
                        print(f"[CYBER//LINK] Sensor Locked: Camera Index [{idx}] (Backend: {backend})")
                        return cap, idx
                cap.release()
            except Exception:
                pass
    return None, -1


# ------------------------------------------------------------------------------
# 7. Core Precision Cyberpunk Virtual Mouse Application
# ------------------------------------------------------------------------------
class CyberVirtualMouseApp:
    def __init__(self):
        self.cam_w = 640
        self.cam_h = 480
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1920, 1080

        # Precision & Control Parameters
        self.ai_smoothing = True
        self.is_frozen = False
        self.sensitivity = 1.4         # Speed multiplier (range 0.8 - 3.5)
        self.user_smoothness = 5.0     # Smoothness factor (range 1 - 10)
        self.margin_x = 95             # Active matrix padding X
        self.margin_y = 75             # Active matrix padding Y
        self.pinch_ratio_mode = 0.28   # Pinch ratio threshold (0.23, 0.28, 0.34)

        # Filters
        self.smoother = AdaptiveSpeedSmoother()
        self.smoother.set_user_smoothness(self.user_smoothness)

        # Aiming stabilization anchor
        self.prev_aim_x = self.cam_w / 2
        self.prev_aim_y = self.cam_h / 2

        # State management
        self.is_dragging = False
        self.last_click_time = 0.0
        self.last_rclick_time = 0.0
        self.last_laction_time = 0.0
        self.last_upaction_time = 0.0
        self.last_downaction_time = 0.0
        self.last_scroll_time = 0.0

        # Flat hand scroll tracking
        self.prev_flat_hand_y = None

        self.action_display_text = ""
        self.action_display_color = None
        self.action_display_timer = 0.0

        # Subsystems
        self.audio = CyberAudio(enabled=True)
        self.hud = CyberHUD()
        self.hand_detector = UniversalHandDetector()

    def trigger_action(self, text, color, sound_name=None, shockwave_pt=None):
        self.action_display_text = text
        self.action_display_color = color
        self.action_display_timer = time.time()
        if sound_name:
            self.audio.play(sound_name)
        if shockwave_pt:
            self.hud.add_shockwave(shockwave_pt[0], shockwave_pt[1], color=color)

    def run(self):
        cap, cam_idx = find_working_camera(self.cam_w, self.cam_h)
        if cap is None:
            print("\n[ERROR] No active camera sensor detected!")
            print("Please ensure your webcam is plugged in and not in use by another application.")
            input("Press Enter to exit...")
            return

        window_name = "CYBER//LINK v2077 - Precision Virtual Air Mouse"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, self.cam_w, self.cam_h)

        self.audio.play("start")
        print("=" * 70)
        print("  [CYBER//LINK v2077] PRECISION DIRECTIONAL AIR MOUSE ONLINE")
        print("=" * 70)
        print(" Gesture Controls:")
        print("  1. CURSOR MOVE       : Index Finger Up (Aiming in-line with hand)")
        print("  2. LEFT CLICK & DRAG : Pinch Thumb + Index Finger (Tap/Hold)")
        print("  3. RIGHT CLICK       : Point Index Sharply to the RIGHT")
        print("  4. LEFT-SIDE ACTION  : Point Index Sharply to the LEFT (Middle-Click)")
        print("  5. UP / DOWN ACTIONS : Point Index Directly UPWARD or DOWNWARD")
        print("  6. FLAT HAND SCROLL  : Flat Hand (all fingers together) - Move Up/Down")
        print(" Hotkeys:")
        print("  * [SPACE]      : Freeze / Pause Cursor Tracking")
        print("  * [<] / [>]    : Sensitivity / Speed Tuning")
        print("  * [-] / [+]    : Smoothness Tuning (1 to 10)")
        print("  * [[] / []]    : Active Matrix Margin Size")
        print("  * [P]          : Cycle Pinch Sensitivity (Firm / Normal / Sensitive)")
        print("  * [S]          : Toggle AI Smoothing")
        print("  * [M]          : Toggle Cyber Audio")
        print("  * [C]          : Toggle CRT Scanlines")
        print("  * [R]          : Recalibrate Camera")
        print("  * [Q] or [ESC] : Disconnect / Exit")
        print("=" * 70)

        p_time = time.time()
        fps = 60.0
        consecutive_dropped = 0

        while True:
            success, frame = cap.read()
            if not success or frame is None:
                consecutive_dropped += 1
                if consecutive_dropped > 45:
                    print("[CYBER//LINK] Optical sensor signal lost.")
                    break
                time.sleep(0.01)
                continue

            consecutive_dropped = 0
            frame = cv2.flip(frame, 1)

            hand_landmarks = self.hand_detector.find_hand(frame)
            self.hud.update_animation()
            self.hud.draw_active_matrix(frame, self.margin_x, self.margin_y, self.cam_w, self.cam_h)

            current_gesture = "IDLE"
            active_pointer_pos = None
            active_dir_mode = "AIM_MOVE"

            if hand_landmarks is not None:
                coords = self.hud.draw_cyber_hand(frame, hand_landmarks, self.cam_w, self.cam_h)

                ix, iy = coords[8]   # Index Tip
                tx, ty = coords[4]   # Thumb Tip
                mx, my = coords[12]  # Middle Tip
                rx, ry = coords[16]  # Ring Tip
                px, py = coords[20]  # Pinky Tip

                # Stabilized aiming anchor
                aim_raw_x = (coords[8][0] * 0.7 + coords[7][0] * 0.3)
                aim_raw_y = (coords[8][1] * 0.7 + coords[7][1] * 0.3)
                self.prev_aim_x += (aim_raw_x - self.prev_aim_x) * 0.85
                self.prev_aim_y += (aim_raw_y - self.prev_aim_y) * 0.85
                aim_x, aim_y = self.prev_aim_x, self.prev_aim_y

                # Distances
                dist_thumb_index = np.hypot(ix - tx, iy - ty)
                dist_index_middle = np.hypot(ix - mx, iy - my)
                dist_middle_ring = np.hypot(mx - rx, my - ry)

                # Palm scale
                palm_scale = max(60.0, np.hypot(coords[0][0] - coords[9][0], coords[0][1] - coords[9][1]))
                scaled_pinch_threshold = palm_scale * self.pinch_ratio_mode

                # Finger states
                thumb_up, index_up, middle_up, ring_up, pinky_up = evaluate_finger_extensions(coords)

                # Check for FLAT HAND sign (all 5 fingers extended together)
                is_flat_hand = (
                    thumb_up and index_up and middle_up and ring_up and pinky_up and
                    (dist_index_middle < palm_scale * 0.40) and
                    (dist_middle_ring < palm_scale * 0.40)
                )

                # Draw distance laser beam
                self.hud.draw_distance_beam(frame, (tx, ty), (ix, iy), dist_thumb_index, threshold_px=scaled_pinch_threshold)

                curr_t = time.time()

                try:
                    # ==========================================================
                    # GESTURE 6: SCROLLING (Flat Hand Sign)
                    # ==========================================================
                    if is_flat_hand:
                        current_gesture = "FLAT_HAND_SCROLL"
                        hand_y = coords[9][1]  # Palm center

                        if self.prev_flat_hand_y is not None:
                            dy = hand_y - self.prev_flat_hand_y
                            if abs(dy) > 2.0:
                                scroll_delta = int(-dy * 2.2)
                                pyautogui.scroll(scroll_delta)
                                if curr_t - self.last_scroll_time > 0.14:
                                    self.audio.play("scroll")
                                    self.last_scroll_time = curr_t
                                dir_str = "UP ▲" if dy < 0 else "DOWN ▼"
                                self.trigger_action(f"SCROLL // {dir_str}", self.hud.YELLOW)

                        self.prev_flat_hand_y = hand_y

                    else:
                        self.prev_flat_hand_y = None

                        # ======================================================
                        # GESTURE 2: LEFT CLICK (Thumb + Index Pinch)
                        # ======================================================
                        if dist_thumb_index < scaled_pinch_threshold:
                            current_gesture = "LEFT_PINCH [CLICK]"
                            active_pointer_pos = (ix, iy)

                            if not self.is_dragging:
                                pyautogui.mouseDown()
                                self.is_dragging = True
                                self.trigger_action("LEFT CLICK // DRAG", self.hud.CYAN, "click", (ix, iy))
                                self.last_click_time = curr_t
                        else:
                            if self.is_dragging:
                                pyautogui.mouseUp()
                                self.is_dragging = False
                                self.trigger_action("DRAG // RELEASE", self.hud.YELLOW, "unlock", (ix, iy))

                            # ==================================================
                            # GESTURES 1, 3, 4, 5: INDEX FINGER (Aim / Point)
                            # ==================================================
                            if index_up and not middle_up and not ring_up and not pinky_up:
                                dir_mode, rel_deg, screen_deg = classify_index_pointing_direction(coords)
                                active_dir_mode = dir_mode

                                # ----------------------------------------------
                                # GESTURE 3: RIGHT CLICK (Pointing Sharply Right)
                                # ----------------------------------------------
                                if dir_mode == "RIGHT_CLICK":
                                    current_gesture = "POINT_RIGHT [R-CLICK]"
                                    active_pointer_pos = (ix, iy)

                                    if curr_t - self.last_rclick_time > 0.50:
                                        pyautogui.rightClick()
                                        self.last_rclick_time = curr_t
                                        self.trigger_action("RIGHT CLICK // EXEC", self.hud.MAGENTA, "right_click", (ix, iy))

                                # ----------------------------------------------
                                # GESTURE 4: LEFT-SIDE ACTION (Pointing Sharply Left)
                                # ----------------------------------------------
                                elif dir_mode == "LEFT_ACTION":
                                    current_gesture = "POINT_LEFT [L-ACTION]"
                                    active_pointer_pos = (ix, iy)

                                    if curr_t - self.last_laction_time > 0.50:
                                        pyautogui.middleClick()  # Standard secondary / middle click
                                        self.last_laction_time = curr_t
                                        self.trigger_action("LEFT-SIDE ACTION // MID-CLICK", self.hud.CYAN, "left_action", (ix, iy))

                                # ----------------------------------------------
                                # GESTURE 5: UP DIRECTIONAL CLICK / ACTION
                                # ----------------------------------------------
                                elif dir_mode == "UP_ACTION":
                                    current_gesture = "POINT_UP [UP-ACTION]"
                                    active_pointer_pos = (ix, iy)

                                    if curr_t - self.last_upaction_time > 0.50:
                                        pyautogui.press("pageup")
                                        self.last_upaction_time = curr_t
                                        self.trigger_action("DIRECTIONAL // UP ACTION", self.hud.GREEN, "up_action", (ix, iy))

                                # ----------------------------------------------
                                # GESTURE 5: DOWN DIRECTIONAL CLICK / ACTION
                                # ----------------------------------------------
                                elif dir_mode == "DOWN_ACTION":
                                    current_gesture = "POINT_DOWN [DOWN-ACTION]"
                                    active_pointer_pos = (ix, iy)

                                    if curr_t - self.last_downaction_time > 0.50:
                                        pyautogui.press("pagedown")
                                        self.last_downaction_time = curr_t
                                        self.trigger_action("DIRECTIONAL // DOWN ACTION", self.hud.YELLOW, "down_action", (ix, iy))

                                # ----------------------------------------------
                                # GESTURE 1: CURSOR MOVEMENT (Smooth Tracking)
                                # ----------------------------------------------
                                else:
                                    current_gesture = "AIM_MOVE"
                                    active_pointer_pos = (int(aim_x), int(aim_y))

                                    if not self.is_frozen:
                                        box_w = self.cam_w - 2 * self.margin_x
                                        box_h = self.cam_h - 2 * self.margin_y
                                        norm_x = (aim_x - self.margin_x) / max(1, box_w)
                                        norm_y = (aim_y - self.margin_y) / max(1, box_h)

                                        scaled_x = 0.5 + (norm_x - 0.5) * self.sensitivity
                                        scaled_y = 0.5 + (norm_y - 0.5) * self.sensitivity

                                        raw_screen_x = scaled_x * self.screen_w
                                        raw_screen_y = scaled_y * self.screen_h

                                        smooth_x, smooth_y = self.smoother.filter(raw_screen_x, raw_screen_y, enabled=self.ai_smoothing)
                                        clamped_x = max(0, min(self.screen_w - 1, int(smooth_x)))
                                        clamped_y = max(0, min(self.screen_h - 1, int(smooth_y)))

                                        pyautogui.moveTo(clamped_x, clamped_y)

                except Exception:
                    pass

                if active_pointer_pos:
                    self.hud.draw_targeting_reticle(frame, active_pointer_pos[0], active_pointer_pos[1], dir_mode=active_dir_mode)

            # Draw Shockwaves & Action Badges
            self.hud.draw_shockwaves(frame)
            if time.time() - self.action_display_timer < 0.85:
                self.hud.draw_action_badge(frame, self.action_display_text, self.action_display_color)

            # Telemetry & Headers
            c_time = time.time()
            fps_inst = 1.0 / max(1e-5, (c_time - p_time))
            fps = 0.9 * fps + 0.1 * fps_inst
            p_time = c_time

            cur_pos_x = self.smoother.prev_x if self.smoother.prev_x else self.screen_w // 2
            cur_pos_y = self.smoother.prev_y if self.smoother.prev_y else self.screen_h // 2

            self.hud.draw_hud_header(frame, fps, mode_text=current_gesture,
                                     sound_on=self.audio.enabled, smoothing_on=self.ai_smoothing,
                                     is_frozen=self.is_frozen)
            self.hud.draw_telemetry_panel(frame, cur_x=cur_pos_x, cur_y=cur_pos_y,
                                          screen_w=self.screen_w, screen_h=self.screen_h,
                                          gesture_name=current_gesture, is_dragging=self.is_dragging,
                                          sensitivity=self.sensitivity, smoothness=self.user_smoothness,
                                          is_frozen=self.is_frozen)
            self.hud.apply_scanlines(frame)

            cv2.imshow(window_name, frame)

            # Check if user closed window by clicking the 'X' button
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    print("[CYBER//LINK] Window closed by user.")
                    break
            except Exception:
                pass

            # ------------------------------------------------------------------
            # Interactive Keyboard Control Handler
            # ------------------------------------------------------------------
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q") or key == 27:
                print("[CYBER//LINK] Disconnected.")
                break
            elif key == 32:  # SPACEBAR: Freeze / Pause cursor
                self.is_frozen = not self.is_frozen
                self.trigger_action("TRACKING FROZEN" if self.is_frozen else "TRACKING RESUMED",
                                    self.hud.RED if self.is_frozen else self.hud.GREEN, "toggle")
                print(f"[CYBER//LINK] Cursor Tracking: {'FROZEN' if self.is_frozen else 'ACTIVE'}")
            elif key == ord(".") or key == ord(">"):  # Increase Sensitivity
                self.sensitivity = min(3.5, self.sensitivity + 0.15)
                self.trigger_action(f"SENSITIVITY: {self.sensitivity:.1f}x", self.hud.YELLOW, "toggle")
            elif key == ord(",") or key == ord("<"):  # Decrease Sensitivity
                self.sensitivity = max(0.8, self.sensitivity - 0.15)
                self.trigger_action(f"SENSITIVITY: {self.sensitivity:.1f}x", self.hud.YELLOW, "toggle")
            elif key == ord("=") or key == ord("+"):  # Increase Smoothness
                self.user_smoothness = min(10.0, self.user_smoothness + 1.0)
                self.smoother.set_user_smoothness(self.user_smoothness)
                self.trigger_action(f"SMOOTHNESS: {int(self.user_smoothness)}/10", self.hud.CYAN, "toggle")
            elif key == ord("-") or key == ord("_"):  # Decrease Smoothness
                self.user_smoothness = max(1.0, self.user_smoothness - 1.0)
                self.smoother.set_user_smoothness(self.user_smoothness)
                self.trigger_action(f"SMOOTHNESS: {int(self.user_smoothness)}/10", self.hud.CYAN, "toggle")
            elif key == ord("]") or key == ord("}"):  # Increase Active Box Margin
                self.margin_x = min(140, self.margin_x + 10)
                self.margin_y = min(110, self.margin_y + 8)
                self.trigger_action(f"FOV INSET: {self.margin_x}px", self.hud.YELLOW, "toggle")
            elif key == ord("[") or key == ord("{"):  # Decrease Active Box Margin (Wider Canvas)
                self.margin_x = max(50, self.margin_x - 10)
                self.margin_y = max(40, self.margin_y - 8)
                self.trigger_action(f"FOV EXPANDED: {self.margin_x}px", self.hud.YELLOW, "toggle")
            elif key == ord("p") or key == ord("P"):  # Cycle Pinch Sensitivity
                modes = [0.23, 0.28, 0.34]
                labels = ["FIRM", "NORMAL", "SENSITIVE"]
                cur_idx = modes.index(self.pinch_ratio_mode) if self.pinch_ratio_mode in modes else 1
                next_idx = (cur_idx + 1) % len(modes)
                self.pinch_ratio_mode = modes[next_idx]
                self.trigger_action(f"PINCH: {labels[next_idx]}", self.hud.CYAN, "toggle")
            elif key == ord("s") or key == ord("S"):  # Toggle AI Smoothing
                self.ai_smoothing = not self.ai_smoothing
                self.trigger_action("AI SMOOTHING: ON" if self.ai_smoothing else "AI SMOOTHING: OFF",
                                    self.hud.CYAN if self.ai_smoothing else self.hud.YELLOW, "toggle")
            elif key == ord("m") or key == ord("M"):  # Toggle Audio
                is_on = self.audio.toggle()
                self.trigger_action("AUDIO: ONLINE" if is_on else "AUDIO: MUTED",
                                    self.hud.GREEN if is_on else self.hud.YELLOW)
            elif key == ord("c") or key == ord("C"):  # Toggle CRT Scanlines
                self.hud.show_scanlines = not self.hud.show_scanlines
                self.trigger_action("SCANLINES: ON" if self.hud.show_scanlines else "SCANLINES: OFF",
                                    self.hud.CYAN)
            elif key == ord("r") or key == ord("R"):  # Recalibrate
                print("[CYBER//LINK] Recalibrating sensors...")
                cap.release()
                cap, cam_idx = find_working_camera(self.cam_w, self.cam_h)

        # Cleanup
        try:
            if self.is_dragging:
                pyautogui.mouseUp()
        except Exception:
            pass
        cap.release()
        cv2.destroyAllWindows()


# ------------------------------------------------------------------------------
# 8. Main Entry Point
# ------------------------------------------------------------------------------
def main():
    app = CyberVirtualMouseApp()
    app.run()


if __name__ == "__main__":
    main()