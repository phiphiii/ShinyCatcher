import cv2
import numpy as np
import time
import os
from gui import utils


def run(capture_device, esp, encounters, shiny_found, is_starter=False):
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

    # Determine how many popups we expect
    target_popups = 2 if is_starter else 1

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
            is_yes_no_visible, _ = utils.detect_popup(current_frame)

            # Dynamic checking: Keep mashing 'A' slowly until the popup appears
            if not is_yes_no_visible:
                if current_time - last_action_time > 0.8:
                    if esp and not utils.TEST_MODE:
                        esp.write(b'A')
                    last_action_time = current_time
            else:
                # Popup detected! Ensure we don't multi-trigger on the same popup
                if current_time - last_popup_time > 2.0:
                    if yes_no_count < target_popups - 1:
                        if esp and not utils.TEST_MODE:
                            esp.write(b'A')
                        yes_no_count += 1
                        last_popup_time = current_time
                        last_action_time = current_time
                    elif yes_no_count == target_popups - 1:
                        # Wait for the YES/NO box animation to fully slide in
                        current_frame = utils.active_sleep(1.2, capture_device, current_frame, "WAIT_POPUP", roi_color,
                                                           mode="GIFT")

                        if esp and not utils.TEST_MODE:
                            # Using explicit hold 'D' and release 'C' instead of tap 'd' for reliability
                            esp.write(b'D')
                            time.sleep(0.1)
                            esp.write(b'C')

                            current_frame = utils.active_sleep(0.4, capture_device, current_frame, "SKIP_NICK",
                                                               roi_color, mode="GIFT")
                            esp.write(b'A')

                        yes_no_count += 1
                        last_popup_time = current_time
                        post_nickname_timer = current_time

            # Proceed to menu after handling all expected popups
            if yes_no_count == target_popups and current_time - post_nickname_timer > 6.0:
                if esp and not utils.TEST_MODE:
                    esp.write(b'C')
                    current_frame = utils.active_sleep(2.0, capture_device, current_frame, "OPENING_MENU", roi_color,
                                                       mode="GIFT")
                    esp.write(b'S')
                    current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_START", roi_color,
                                                       mode="GIFT")

                    if not is_starter:
                        # Using explicit hold 'D' and release 'C' to navigate down
                        esp.write(b'D')
                        time.sleep(0.1)
                        esp.write(b'C')
                        current_frame = utils.active_sleep(0.5, capture_device, current_frame, "MENU_DOWN", roi_color,
                                                           mode="GIFT")

                    esp.write(b'A')
                    current_frame = utils.active_sleep(2.0, capture_device, current_frame, "MENU_POKEMON", roi_color,
                                                       mode="GIFT")

                if not is_starter:
                    state = "CHECK_PARTY"
                else:
                    if esp and not utils.TEST_MODE:
                        esp.write(b'A')
                        current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_SELECT", roi_color,
                                                           mode="GIFT")
                        esp.write(b'A')
                        current_frame = utils.active_sleep(3.0, capture_device, current_frame, "MENU_SUMMARY",
                                                           (0, 255, 0), mode="GIFT")
                    state = "CHECKING_SHINY"

            # Failsafe reboot
            if current_time - fail_safe_timer > 75.0:
                state = "RESETTING"

        elif state == "CHECK_PARTY":
            # Special state for Eevee to scroll down the party
            is_at_bottom = utils.detect_party_bottom_cursor(current_frame)

            if is_at_bottom:
                if esp and not utils.TEST_MODE:
                    esp.write(b'A')
                    current_frame = utils.active_sleep(1.5, capture_device, current_frame, "MENU_SELECT", roi_color,
                                                       mode="GIFT")
                    esp.write(b'A')  # Select SUMMARY
                    current_frame = utils.active_sleep(3.0, capture_device, current_frame, "MENU_SUMMARY", (0, 255, 0),
                                                       mode="GIFT")
                state = "CHECKING_SHINY"
            else:
                if esp and not utils.TEST_MODE:
                    esp.write(b'd')
                    current_frame = utils.active_sleep(0.4, capture_device, current_frame, "MOVING_DOWN", roi_color,
                                                       mode="GIFT")



        elif state == "RESETTING":

            if esp and not utils.TEST_MODE:
                esp.write(b'A')
                current_frame = utils.active_sleep(1.0, capture_device, current_frame, "WAKE_UP", roi_color,
                                                   mode="GIFT")
                esp.write(b'H')
                current_frame = utils.active_sleep(1.5, capture_device, current_frame, "RESET_HOME", roi_color,
                                                   mode="GIFT")
                esp.write(b'X')
                current_frame = utils.active_sleep(0.5, capture_device, current_frame, "RESET_X", roi_color,
                                                   mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(4.0, capture_device, current_frame, "CLOSING_GAME", roi_color,
                                                   mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(1.5, capture_device, current_frame, "SELECT_USER", roi_color,
                                                   mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(12.0, capture_device, current_frame, "LOADING_GAME", roi_color,
                                                   mode="GIFT")
                esp.write(b'A')

                current_frame = utils.active_sleep(2.5, capture_device, current_frame, "TITLE_SCREEN", roi_color,
                                                   mode="GIFT")
                esp.write(b'A')
                current_frame = utils.active_sleep(4.0, capture_device, current_frame, "ENTERING_WORLD", roi_color,
                                                   mode="GIFT")

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
            cv2.putText(current_frame, 'SHINY_DETECTED_ALARM_ON', (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255),
                        3)

        if state != "RESETTING" and "MENU" not in state:
            cv2.rectangle(current_frame, (utils.ROI_X, utils.ROI_Y),
                          (utils.ROI_X + utils.ROI_W, utils.ROI_Y + utils.ROI_H), roi_color, 2)

            if state == "NAVIGATE_PARTY_BOTTOM":
                cv2.rectangle(current_frame, (utils.PARTY_BOTTOM_ROI_X, utils.PARTY_BOTTOM_ROI_Y),
                              (utils.PARTY_BOTTOM_ROI_X + utils.PARTY_BOTTOM_ROI_W,
                               utils.PARTY_BOTTOM_ROI_Y + utils.PARTY_BOTTOM_ROI_H), (255, 255, 0), 2)

            # Prepare UI statistics dictionary instead of drawing text on OpenCV frame
            ui_data = {
                'status': state,
                'encounters': encounters,
                'shiny_found': shiny_found,
                'wait_time': "  - "  # Clear wait time if not in sleep phase
            }

            utils.display_frame(current_frame, mask, ui_kwargs=ui_data)

        if utils.STOP_FLAG:
            break