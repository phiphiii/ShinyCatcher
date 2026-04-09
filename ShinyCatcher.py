import cv2
import numpy as np
import time

TEST_MODE = True
TEST_IMAGE_PATH = 'shiny_charmander.webp'

ROI_X = 800
ROI_Y = 250
ROI_W = 80
ROI_H = 80


def detect_gift_shiny(frame):
    star_roi = frame[ROI_Y:ROI_Y + ROI_H, ROI_X:ROI_X + ROI_W]
    hsv_roi = cv2.cvtColor(star_roi, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([35, 255, 255])

    yellow_mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
    yellow_pixel_count = cv2.countNonZero(yellow_mask)

    return yellow_pixel_count > 15, yellow_mask


def main():
    if not TEST_MODE:
        capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        capture_device.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    while True:
        if not TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                break
        else:
            current_frame = cv2.imread(TEST_IMAGE_PATH)
            if current_frame is None:
                print("ERROR: Image not found.")
                break
            time.sleep(0.05)

        is_shiny, mask = detect_gift_shiny(current_frame)

        cv2.rectangle(current_frame, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), (0, 255, 0), 2)

        if is_shiny:
            cv2.putText(current_frame, 'SHINY DETECTED', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 215, 255), 3)

        resized_frame = cv2.resize(current_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Switch Stream', resized_frame)
        cv2.imshow('Yellow Mask', mask)

        key_pressed = cv2.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

    if not TEST_MODE:
        capture_device.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()