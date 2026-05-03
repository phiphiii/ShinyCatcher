import platform
import cv2
import numpy as np
import time
import os
import serial
import sys
import json

TEST_MODE = False
TEST_IMAGE_PATH = 'testing_img/shiny_charmander.webp'
COUNTER_FILE = 'encounters.json'

current_system = platform.system()
if current_system == "Windows":
    PORT_COM = "COM11"
elif current_system == "Darwin":
    PORT_COM = "/dev/cu.usbmodem5ABA0203801"
else:
    PORT_COM = "/dev/ttyUSB0"

ROI_X = 825
ROI_Y = 220
ROI_W = 80
ROI_H = 80

POPUP_ROI_X = 1250
POPUP_ROI_Y = 500
POPUP_ROI_W = 300
POPUP_ROI_H = 250
WHITE_PIXELS_THRESHOLD = 8000

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

def active_sleep(seconds, capture_device, current_frame, state_name="WAITING", box_color=(0, 0, 255)):
    start_time = time.time()
    latest_frame = current_frame.copy() if current_frame is not None else np.zeros((1080, 1920, 3), dtype=np.uint8)
    while time.time() - start_time < seconds:
        disp_frame = latest_frame.copy()
        if not TEST_MODE and capture_device:
            is_read, frame = capture_device.read()
            if is_read:
                disp_frame = frame.copy()
                latest_frame = frame.copy()

        cv2.rectangle(disp_frame, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), box_color, 2)
        cv2.rectangle(disp_frame, (POPUP_ROI_X, POPUP_ROI_Y), (POPUP_ROI_X + POPUP_ROI_W, POPUP_ROI_Y + POPUP_ROI_H),
                      (255, 0, 0), 2)

        cv2.putText(disp_frame, f'Status: {state_name}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
        cv2.putText(disp_frame, f'Wait: {time.time() - start_time:.1f}s / {seconds:.1f}s', (30, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
        resized = cv2.resize(disp_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Stream', resized)
        cv2.waitKey(10)
    return latest_frame

def start_hunting():
    cv2.namedWindow('Nintendo Stream')
    encounters, shiny_found = load_counter()

    try:
        esp = serial.Serial(PORT_COM, 115200, timeout=0.1, write_timeout=0)
        time.sleep(6)
        if esp and not TEST_MODE:
            esp.write(b'F')
            time.sleep(0.5)
    except Exception as e:
        print(f"BLAD PORTU: {e}")
        esp = None

    capture_device = None
    if not TEST_MODE:
        if current_system == "Windows":
            capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            capture_device = cv2.VideoCapture(0)

        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        capture_device.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    state = "RESETTING"
    last_action_time = time.time()
    mask = np.zeros((ROI_H, ROI_W), dtype=np.uint8)

    checking_phase_start = 0
    yes_no_count = 0
    post_nickname_timer = 0
    white_px_count = 0
    fail_safe_timer = time.time()
    last_popup_time = 0
    phase_start_time = time.time()

    while True:
        if not TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                break
        else:
            if not os.path.exists(TEST_IMAGE_PATH):
                break
            current_frame = cv2.imread(TEST_IMAGE_PATH)
            current_frame = cv2.resize(current_frame, (1920, 1080))
            time.sleep(0.01)

        current_time = time.time()
        roi_color = (0, 0, 255)

        if state == "MASHING_A":
            is_yes_no_visible = False

            if current_time - phase_start_time > 10.0:
                is_yes_no_visible, white_px_count = detect_popup(current_frame)

            if is_yes_no_visible and current_time - last_popup_time > 3.0:
                if yes_no_count == 0:
                    if esp and not TEST_MODE:
                        esp.write(b'A')
                    yes_no_count += 1
                    last_popup_time = current_time
                    last_action_time = current_time
                    fail_safe_timer = current_time

                elif yes_no_count == 1:
                    if esp and not TEST_MODE:
                        esp.write(b'd')
                        current_frame = active_sleep(0.3, capture_device, current_frame, "SKIPPING_NICKNAME", roi_color)
                        esp.write(b'A')
                    yes_no_count += 1
                    last_popup_time = current_time
                    last_action_time = current_time
                    post_nickname_timer = current_time

            elif current_time - last_action_time > 0.6:
                if current_time - last_popup_time > 1.5:
                    if esp and not TEST_MODE:
                        esp.write(b'A')
                    last_action_time = current_time

            if yes_no_count == 2 and current_time - post_nickname_timer > 6.0:
                if esp and not TEST_MODE:
                    esp.write(b'C')
                    current_frame = active_sleep(2.0, capture_device, current_frame, "OPENING_MENU", roi_color)
                    esp.write(b'S')
                    current_frame = active_sleep(1.5, capture_device, current_frame, "MENU_START", roi_color)
                    esp.write(b'A')
                    current_frame = active_sleep(1.5, capture_device, current_frame, "MENU_POKEMON", roi_color)
                    esp.write(b'A')
                    current_frame = active_sleep(1.5, capture_device, current_frame, "MENU_SELECT", roi_color)
                    esp.write(b'A')
                    current_frame = active_sleep(3.0, capture_device, current_frame, "MENU_SUMMARY", (0, 255, 0))
                state = "CHECKING_SHINY"

            if current_time - fail_safe_timer > 75.0:
                state = "RESETTING"

        elif state == "RESETTING":
            if esp and not TEST_MODE:
                esp.write(b'A')
                current_frame = active_sleep(1.0, capture_device, current_frame, "WAKE_UP_CONTROLLER", roi_color)
                esp.write(b'H')
                current_frame = active_sleep(1.5, capture_device, current_frame, "RESET_HOME", roi_color)
                esp.write(b'X')
                current_frame = active_sleep(0.5, capture_device, current_frame, "RESET_X", roi_color)
                esp.write(b'A')
                current_frame = active_sleep(4.0, capture_device, current_frame, "RESET_CLOSING_GAME", roi_color)
                esp.write(b'A')
                current_frame = active_sleep(1.5, capture_device, current_frame, "RESET_SELECT_USER", roi_color)
                esp.write(b'A')
                current_frame = active_sleep(12.0, capture_device, current_frame, "RESET_LOADING_GAME", roi_color)
            state = "MASHING_A"
            yes_no_count = 0
            post_nickname_timer = 0
            fail_safe_timer = time.time()
            last_popup_time = 0
            phase_start_time = time.time()

        elif state == "CHECKING_SHINY":
            if checking_phase_start == 0:
                checking_phase_start = current_time
                encounters += 1
                save_counter(encounters, shiny_found)
            roi_color = (0, 255, 0)
            is_shiny, mask_yellow = detect_gift_shiny(current_frame)
            mask = mask_yellow
            if is_shiny:
                state = "SHINY_FOUND"
                shiny_found += 1
                save_counter(encounters, shiny_found)
                checking_phase_start = 0
            elif current_time - checking_phase_start > 3.0:
                state = "RESETTING"
                checking_phase_start = 0

        elif state == "SHINY_FOUND":
            if esp and not TEST_MODE:
                esp.write(b'Q')
            state = "STOPPED"

        elif state == "STOPPED":
            roi_color = (0, 255, 0)
            cv2.putText(current_frame, 'SHINY_DETECTED_ALARM_ON', (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255),
                        3)

        if state != "RESETTING" and "MENU" not in state:
            cv2.rectangle(current_frame, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), roi_color, 2)

            if state == "MASHING_A":
                cv2.rectangle(current_frame, (POPUP_ROI_X, POPUP_ROI_Y),
                              (POPUP_ROI_X + POPUP_ROI_W, POPUP_ROI_Y + POPUP_ROI_H), (255, 0, 0), 2)
                cv2.putText(current_frame, f'White Px: {white_px_count}', (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                            (255, 100, 255), 2)
                cv2.putText(current_frame, f'Popups: {yes_no_count}/2', (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                            (100, 255, 100), 2)

            cv2.putText(current_frame, f'Status: {state}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(current_frame, f'Encounters: {encounters}', (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 255, 255), 2)
            cv2.putText(current_frame, f'Shiny Found: {shiny_found}', (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 215, 255), 2)

            resized_frame = cv2.resize(current_frame, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow('Nintendo Stream', resized_frame)
            cv2.imshow('Yellow Mask', mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if capture_device:
        capture_device.release()
    if esp:
        if not TEST_MODE:
            esp.write(b'F')
        esp.close()

    cv2.destroyAllWindows()
    cv2.waitKey(1)

def main():
    global TEST_MODE
    while True:
        choice = input("1. Start Gift Hunting\n2. Start Test Mode\n3. Exit\nChoose: ")
        if choice == '1':
            TEST_MODE = False
            start_hunting()
        elif choice == '2':
            TEST_MODE = True
            start_hunting()
        elif choice == '3':
            sys.exit()

if __name__ == "__main__":
    main()