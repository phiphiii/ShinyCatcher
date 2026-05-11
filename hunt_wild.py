import cv2
import numpy as np
import time
import utils


def run(capture_device, esp, encounters, shiny_found):
    state = "SPINNING"
    yellow_history = []
    phase_start_time = time.time()
    mask = np.zeros((500, 920), dtype=np.uint8)
    delta = 0

    while True:
        if utils.TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                capture_device.set(cv2.CAP_PROP_POS_FRAMES, 0)
                is_frame_read, current_frame = capture_device.read()
                if not is_frame_read: break
            current_frame = cv2.resize(current_frame, (1920, 1080))
            time.sleep(0.03)
        else:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read: break
            current_frame = cv2.resize(current_frame, (1920, 1080))

        current_time = time.time()
        roi_color = (0, 0, 255)
        disp_frame = current_frame.copy()

        if state == "SPINNING":
            roi_color = (0, 0, 255)
            if esp and not utils.TEST_MODE:
                """
                current_frame = utils.active_sleep(0.35, capture_device, current_frame, "SPINNING", roi_color, break_on_black=True, mode="WILD")
                esp.write(b'l')
                esp.write(b'u')
                esp.write(b'r')
                esp.write(b'd')
                """
                esp.write(b'l')
                # Wait for walking animation to finish. Break instantly if battle starts.
                current_frame = utils.active_sleep(0.6, capture_device, current_frame, "STEP_LEFT", roi_color, break_on_black=True, mode="WILD")

                # If battle hasn't started, take one step right back to the original spot
                if not utils.detect_black_screen(current_frame):
                    esp.write(b'r')
                    current_frame = utils.active_sleep(0.6, capture_device, current_frame, "STEP_RIGHT", roi_color, break_on_black=True, mode="WILD")


            if utils.detect_black_screen(current_frame):
                state = "CHECKING_WILD_SHINY"
                phase_start_time = current_time
                yellow_history.clear()
                delta = 0
                if not utils.TEST_MODE:
                    encounters += 1
                    utils.save_counter(encounters, shiny_found)

        elif state == "CHECKING_WILD_SHINY":
            roi_color = (0, 255, 0)
            mask, yellow_count = utils.detect_wild_shiny(current_frame)
            time_in_battle = current_time - phase_start_time

            if time_in_battle < 1.5:
                cv2.putText(disp_frame, 'WAITING FOR SLIDE-IN...', (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (0, 165, 255), 2)
            else:
                yellow_history.append(yellow_count)
                if len(yellow_history) > 15: yellow_history.pop(0)
                if len(yellow_history) >= 5:
                    delta = yellow_count - min(yellow_history)
                    if delta > 800:
                        state = "SHINY_FOUND"
                        if not utils.TEST_MODE:
                            shiny_found += 1
                            utils.save_counter(encounters, shiny_found)

            if time_in_battle > 6.0:
                state = "ESCAPING"
                esp.write(b'A')

        elif state == "ESCAPING":
            current_frame = utils.active_sleep(2.8, capture_device, current_frame, "THROWING_POKEMON", roi_color,
                                               mode="WILD")

            roi_color = (255, 100, 0)
            if esp and not utils.TEST_MODE:
                #current_frame = utils.active_sleep(2.5, capture_device, current_frame, "ESCAPING", roi_color,mode="WILD")
                esp.write(b'r')
                esp.write(b'd')
                esp.write(b'A')
                current_frame = utils.active_sleep(2.0, capture_device, current_frame, "ESCAPE_CLICK", roi_color,
                                                   mode="WILD")
                esp.write(b'A')
                current_frame = utils.active_sleep(3.5, capture_device, current_frame, "ESCAPE_WAIT", roi_color,
                                                   mode="WILD")

            state = "SPINNING"

        elif state == "SHINY_FOUND":
            if esp: esp.write(b'Q')
            state = "STOPPED"

        elif state == "STOPPED":
            roi_color = (0, 255, 0)
            cv2.putText(disp_frame, 'SHINY_DETECTED_ALARM_ON', (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        cv2.rectangle(disp_frame, (1000, 0), (1920, 500), roi_color, 2)
        cv2.putText(disp_frame, f'Status: {state}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(disp_frame, f'Encounters: {encounters}', (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
        cv2.putText(disp_frame, f'Shiny Found: {shiny_found}', (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 215, 255),
                    2)

        if state == "SPINNING":
            roi_black = current_frame[300:780, 500:1420]
            mean_black = np.mean(roi_black)
            cv2.putText(disp_frame, f'Blackness: {mean_black:.1f} / 45', (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (100, 255, 255), 2)
        elif state == "CHECKING_WILD_SHINY":
            cv2.putText(disp_frame, f'Delta: {delta} / 800', (30, 185), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 100, 255),
                        2)

        resized_frame = cv2.resize(disp_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Stream', resized_frame)
        mask_resized = cv2.resize(mask, (0, 0), fx=1.0, fy=1.0)
        cv2.imshow('Yellow Mask', mask_resized)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break