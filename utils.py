import platform
import cv2
import numpy as np
import time
import os
import json

# --- GLOBAL CONFIGURATION ---
TEST_MODE = False
TEST_IS_VIDEO = False
TEST_IMAGE_PATH = 'testing_img/shiny_charmander.webp'
TEST_VIDEO_PATH = 'testing_img/shiny_wild_ekans_ex.mp4'
COUNTER_FILE = 'encounters.json'

current_system = platform.system()
if current_system == "Windows":
    PORT_COM = "COM11"
elif current_system == "Darwin":
    PORT_COM = "/dev/cu.usbmodem5ABA0203801"
else:
    PORT_COM = "/dev/ttyUSB0"

# --- REGIONS OF INTEREST (ROI) & THRESHOLDS ---
ROI_X = 825
ROI_Y = 220
ROI_W = 80
ROI_H = 80

POPUP_ROI_X = 1250
POPUP_ROI_Y = 500
POPUP_ROI_W = 300
POPUP_ROI_H = 250
WHITE_PIXELS_THRESHOLD = 8000

BITE_ROI_X = 600
BITE_ROI_Y = 850
BITE_ROI_W = 700
BITE_ROI_H = 150
BITE_PIXELS_THRESHOLD = 3000


# --- HELPER FUNCTIONS ---
def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as file_handler:
            try:
                data = json.load(file_handler)
                return data.get('encounters', 0), data.get('shiny_found', 0)
            except:
                return 0, 0
    return 0, 0


def save_counter(encounters, shiny_found):
    with open(COUNTER_FILE, 'w') as file_handler:
        json.dump({'encounters': encounters, 'shiny_found': shiny_found}, file_handler)


def detect_gift_shiny(frame):
    star_roi = frame[ROI_Y:ROI_Y + ROI_H, ROI_X:ROI_X + ROI_W]
    hsv_roi = cv2.cvtColor(star_roi, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([40, 255, 255])
    mask_yellow = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
    yellow_pixels = cv2.countNonZero(mask_yellow)
    return yellow_pixels > 15, mask_yellow


def detect_popup(frame):
    popup_roi = frame[POPUP_ROI_Y:POPUP_ROI_Y + POPUP_ROI_H, POPUP_ROI_X:POPUP_ROI_X + POPUP_ROI_W]
    hsv_popup = cv2.cvtColor(popup_roi, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 40, 255])
    mask_white = cv2.inRange(hsv_popup, lower_white, upper_white)
    white_pixels = cv2.countNonZero(mask_white)
    return white_pixels > WHITE_PIXELS_THRESHOLD, white_pixels


def detect_bite(frame):
    bite_roi = frame[BITE_ROI_Y:BITE_ROI_Y + BITE_ROI_H, BITE_ROI_X:BITE_ROI_X + BITE_ROI_W]
    hsv_bite = cv2.cvtColor(bite_roi, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 40, 255])
    mask_white = cv2.inRange(hsv_bite, lower_white, upper_white)
    white_pixels = cv2.countNonZero(mask_white)
    return white_pixels > BITE_PIXELS_THRESHOLD, white_pixels


def detect_black_screen(frame):
    roi = frame[300:780, 500:1420]
    mean_val = np.mean(roi)
    return mean_val < 45


def detect_wild_shiny(frame):
    roi = frame[0:500, 1000:1920]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([30, 160, 200])
    upper_yellow = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    return mask, cv2.countNonZero(mask)


def detect_fishing_shiny(frame):
    roi = frame[0:500, 1000:1920]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([30, 170, 200])
    upper_yellow = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    return mask, cv2.countNonZero(mask)


def active_sleep(seconds, capture_device, current_frame, state_name="WAITING", box_color=(0, 0, 255),
                 break_on_black=False, mode="NONE"):
    start_time = time.time()
    latest_frame = current_frame.copy() if current_frame is not None else np.zeros((1080, 1920, 3), dtype=np.uint8)

    while time.time() - start_time < seconds:
        disp_frame = latest_frame.copy()
        if (not TEST_MODE or TEST_IS_VIDEO) and capture_device:
            is_read, frame = capture_device.read()
            if is_read:
                frame = cv2.resize(frame, (1920, 1080))
                disp_frame = frame.copy()
                latest_frame = frame.copy()
            elif TEST_IS_VIDEO:
                capture_device.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Ninja Reflex: Interrupt sleep immediately if black screen is detected
        if break_on_black and detect_black_screen(latest_frame):
            break

        # Draw specific bounding boxes based on the active hunting mode
        if mode == "GIFT":
            cv2.rectangle(disp_frame, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), box_color, 2)
            cv2.rectangle(disp_frame, (POPUP_ROI_X, POPUP_ROI_Y),
                          (POPUP_ROI_X + POPUP_ROI_W, POPUP_ROI_Y + POPUP_ROI_H), (255, 0, 0), 2)
        elif mode == "WILD":
            cv2.rectangle(disp_frame, (1000, 0), (1920, 500), box_color, 2)
        elif mode == "FISH":
            cv2.rectangle(disp_frame, (1000, 0), (1920, 500), box_color, 2)
            if state_name == "WAITING_FOR_BITE":
                cv2.rectangle(disp_frame, (BITE_ROI_X, BITE_ROI_Y), (BITE_ROI_X + BITE_ROI_W, BITE_ROI_Y + BITE_ROI_H),
                              (255, 0, 0), 2)

        cv2.putText(disp_frame, f'Status: {state_name}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
        cv2.putText(disp_frame, f'Wait: {time.time() - start_time:.1f}s / {seconds:.1f}s', (30, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        resized = cv2.resize(disp_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Stream', resized)
        cv2.waitKey(10)
    return latest_frame