import cv2
import numpy as np
import time
import os
from gui import utils


def run(capture_device, esp, encounters, shiny_found):
    state = "RESETTING"
    last_action_time = time.time()
    mask = np.zeros((utils.ROI_H, utils.ROI_W), dtype=np.uint8)
    checking_phase_start = 0
    yes_no_count = 0
    post_nickname_timer = 0
    white_px_count = 0
    fail_safe_timer = time.time()
    last_popup_time = 0
    phase_start_time = time.time()

    while True:
        if not utils.TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                break
            current_frame = cv2.resize(current_frame, (1920, 1080))
        else:
            if not os.path.exists(utils.TEST_IMAGE_PATH):
                break
            current_frame = cv2.imread(utils.TEST_IMAGE_PATH)
            current_frame = cv2.resize(current_frame, (1920, 1080))
            time.sleep(0.01)

        current_time = time.time()
        roi_color = (0, 0, 255)

        if state == "MASHING_A":
            is_yes_no_visible = False
            if current_time - phase_start_time > 10.0:
                is_yes_no_visible, white_px_count = utils.detect_popup(current_frame)
            if is_yes_no_visible and current_time - last_popup_time > 3.0:
                if yes_no_count == 0:
                    if esp and not utils.TEST_MODE: esp.write(b'A')
                    yes_no_count += 1
                    last_popup_time = current_time
                    last_action_time = current_time
                    fail_safe_timer = current_time
                elif yes_no_count == 1:
                    if esp and not utils.TEST_MODE:
                        esp.write(b'd')
                        current_frame = utils.active_sleep(0.3, capture_device, current_frame, "SKIPPING_NICKNAME", roi_color, mode="GIFT")
                        esp.write(b'A')
                    yes_no_count += 1
                    last_popup_time = current_time
                    last_action_time = current_time
                    post_nickname_timer = current_time
            elif current_time - last_action_time > 0.6:
                if current_time - last_popup_time > 1.5:
                    if esp and not utils.TEST_MODE: esp.write(b'A')
                    last_action_time = current_time
            if yes_no_count == 2 and current_time - post_nickname_timer > 6.0:
                if esp and not utils.TEST_MODE:
                    esp.write(b'C')
                    current_frame = utils.active_sleep(2.0, capture_device, current_frame, "OPENING_MENU", roi_color, mode="GIFT")
                    esp.write(b'S')
                    current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_START", roi_color, mode="GIFT")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_POKEMON", roi_color, mode="GIFT")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_SELECT", roi_color, mode="GIFT")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(3.0, capture_device, current_frame, "MENU_SUMMARY", (0, 255, 0), mode="GIFT")
                state = "CHECKING_SHINY"
            if current_time - fail_safe_timer > 75.0:
                state = "RESETTING"

        elif state == "RESETTING":
            if esp and not utils.TEST_MODE:
                esp.write(b'A')
                current_frame = utils.active_sleep(1.0, capture_device, current_frame, "WAKE_UP_CONTROLLER", roi_color, mode="GIFT")
                esp.write(b'H')
                current_frame = utils.active_sleep(1.5, capture_device, current_frame, "RESET_HOME", roi_color, mode="GIFT")
                esp.write(b'X')
                current_frame = utils.active_sleep(0.5, capture_device, current_frame, "RESET_X", roi_color, mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(4.0, capture_device, current_frame, "RESET_CLOSING_GAME", roi_color, mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(1.5, capture_device, current_frame, "RESET_SELECT_USER", roi_color, mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(12.0, capture_device, current_frame, "RESET_LOADING_GAME", roi_color, mode="GIFT")
            state = "MASHING_A"
            yes_no_count = 0
            post_nickname_timer = 0
            fail_safe_timer = time.time()
            last_popup_time = 0
            phase_start_time = time.time()

        elif state == "CHECKING_SHINY":
            if checking_phase_start == 0:
                checking_phase_start = current_time
                if not utils.TEST_MODE:
                    encounters += 1
                    utils.save_counter(encounters, shiny_found)
            roi_color = (0, 255, 0)
            is_shiny, mask_yellow = utils.detect_gift_shiny(current_frame)
            mask = mask_yellow
            if is_shiny:
                state = "SHINY_FOUND"
                if not utils.TEST_MODE:
                    shiny_found += 1
                    utils.save_counter(encounters, shiny_found)
                checking_phase_start = 0
            elif current_time - checking_phase_start > 3.0:
                state = "RESETTING"
                checking_phase_start = 0

        elif state == "SHINY_FOUND":
            if esp: esp.write(b'Q')
            state = "STOPPED"

        elif state == "STOPPED":
            roi_color = (0, 255, 0)
            cv2.putText(current_frame, 'SHINY_DETECTED_ALARM_ON', (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        if state != "RESETTING" and "MENU" not in state:
            cv2.rectangle(current_frame, (utils.ROI_X, utils.ROI_Y), (utils.ROI_X + utils.ROI_W, utils.ROI_Y + utils.ROI_H), roi_color, 2)
            cv2.putText(current_frame, f'Status: {state}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(current_frame, f'Encounters: {encounters}', (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
            cv2.putText(current_frame, f'Shiny Found: {shiny_found}', (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 215, 255), 2)
            resized_frame = cv2.resize(current_frame, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow('Nintendo Stream', resized_frame)
            cv2.imshow('Yellow Mask', mask)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break