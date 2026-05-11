import cv2
import numpy as np
import time
import utils

def run(capture_device, esp, encounters, shiny_found):
    state = "CASTING_ROD"
    yellow_history = []
    phase_start_time = time.time()
    mask = np.zeros((500, 920), dtype=np.uint8)
    delta = 0
    bite_timer = time.time()
    white_px_count = 0

    is_first_cast = True
    last_text_interaction = 0

    while True:
        if utils.TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                capture_device.set(cv2.CAP_PROP_POS_FRAMES, 0)
                is_frame_read, current_frame = capture_device.read()
                if not is_frame_read:
                    print("\n[ERROR] Cannot read frames from video file!")
                    break
            current_frame = cv2.resize(current_frame, (1920, 1080))
            time.sleep(0.03)
        else:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                break
            current_frame = cv2.resize(current_frame, (1920, 1080))

        current_time = time.time()
        roi_color = (0, 0, 255)
        disp_frame = current_frame.copy()

        if state == "CASTING_ROD":
            roi_color = (0, 0, 255)

            if esp and not utils.TEST_MODE:
                if is_first_cast:
                    esp.write(b'S')
                    current_frame = utils.active_sleep(1.2, capture_device, current_frame, "MENU_OPEN", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(1.0, capture_device, current_frame, "BAG_OPEN", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(0.6, capture_device, current_frame, "SELECT_ROD", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(3.5, capture_device, current_frame, "CASTING", roi_color, mode="FISH")

                    is_first_cast = False
                else:
                    esp.write(b'S')
                    current_frame = utils.active_sleep(0.8, capture_device, current_frame, "MENU_OPEN", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(0.8, capture_device, current_frame, "BAG_OPEN", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(0.6, capture_device, current_frame, "SELECT_ROD", roi_color, mode="FISH")
                    esp.write(b'A')
                    current_frame = utils.active_sleep(3.5, capture_device, current_frame, "CASTING", roi_color, mode="FISH")

            state = "WAITING_FOR_BITE"
            bite_timer = time.time()
            last_text_interaction = 0

        elif state == "WAITING_FOR_BITE":
            roi_color = (255, 255, 0)
            is_text_visible, white_px_count = utils.detect_bite(current_frame)

            if is_text_visible:
                if current_time - last_text_interaction > 0.4:
                    if esp and not utils.TEST_MODE:
                        esp.write(b'A')
                    last_text_interaction = current_time

            if utils.detect_black_screen(current_frame):
                state = "CHECKING_WILD_SHINY"
                phase_start_time = current_time
                yellow_history.clear()
                delta = 0
                if not utils.TEST_MODE:
                    encounters += 1
                    utils.save_counter(encounters, shiny_found)

            elif current_time - bite_timer > 15.0 or (last_text_interaction > 0 and current_time - last_text_interaction > 3.5):
                state = "CASTING_ROD"

        elif state == "CHECKING_WILD_SHINY":
            roi_color = (0, 255, 0)
            mask, yellow_count = utils.detect_fishing_shiny(current_frame)
            time_in_battle = current_time - phase_start_time

            if time_in_battle < 1.5:
                cv2.putText(disp_frame, 'WAITING FOR SLIDE-IN...', (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
            else:
                yellow_history.append(yellow_count)
                if len(yellow_history) > 15:
                    yellow_history.pop(0)

                if len(yellow_history) >= 5:
                    delta = yellow_count - min(yellow_history)
                    if delta > 800:
                        state = "SHINY_FOUND"
                        if not utils.TEST_MODE:
                            shiny_found += 1
                            utils.save_counter(encounters, shiny_found)

            if time_in_battle > 7.0:
                state = "ESCAPING"

        elif state == "ESCAPING":
            roi_color = (255, 100, 0)
            if esp and not utils.TEST_MODE:
                esp.write(b'r')
                current_frame = utils.active_sleep(0.5, capture_device, current_frame, "ESCAPE_RIGHT", roi_color, mode="FISH")
                esp.write(b'd')
                current_frame = utils.active_sleep(0.5, capture_device, current_frame, "ESCAPE_DOWN", roi_color, mode="FISH")
                esp.write(b'A')
                current_frame = utils.active_sleep(4.0, capture_device, current_frame, "ESCAPE_WAIT", roi_color, mode="FISH")
            state = "CASTING_ROD"

        elif state == "SHINY_FOUND":
            if esp:
                esp.write(b'Q')
            state = "STOPPED"

        elif state == "STOPPED":
            roi_color = (0, 255, 0)
            cv2.putText(disp_frame, 'SHINY_DETECTED_ALARM_ON', (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        cv2.rectangle(disp_frame, (1000, 0), (1920, 500), roi_color, 2)
        if state == "WAITING_FOR_BITE":
            cv2.rectangle(disp_frame, (utils.BITE_ROI_X, utils.BITE_ROI_Y), (utils.BITE_ROI_X + utils.BITE_ROI_W, utils.BITE_ROI_Y + utils.BITE_ROI_H), (255, 0, 0), 2)
            cv2.putText(disp_frame, f'Bite Px: {white_px_count}', (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 100, 255), 2)

        cv2.putText(disp_frame, f'Status: {state}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(disp_frame, f'Encounters: {encounters}', (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
        cv2.putText(disp_frame, f'Shiny Found: {shiny_found}', (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 215, 255), 2)

        if state == "CHECKING_WILD_SHINY":
            cv2.putText(disp_frame, f'Delta: {delta} / 800', (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 100, 255), 2)

        resized_frame = cv2.resize(disp_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Stream', resized_frame)
        mask_resized = cv2.resize(mask, (0, 0), fx=1.0, fy=1.0)
        cv2.imshow('Yellow Mask', mask_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break