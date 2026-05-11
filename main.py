import cv2
import serial
import time
import os
import sys
import utils

# Import module for manual mode.
# Hunting modules will be imported here in the future.
import manual
import hunt_gift
import hunt_wild
import hunt_fish

def start_engine(hunting_mode="MANUAL"):
    """Initializes hardware connection and routes to the correct module."""

    # Configure test video fallback if necessary
    if hunting_mode in ["WILD", "FISH"] and utils.TEST_MODE:
        utils.TEST_IS_VIDEO = True
        if not os.path.exists(utils.TEST_VIDEO_PATH):
            print(f"\n[ERROR] Video file not found: {utils.TEST_VIDEO_PATH}")
            return
    else:
        utils.TEST_IS_VIDEO = False

    cv2.namedWindow('Nintendo Stream')
    encounters, shiny_found = utils.load_counter()

    # Attempt serial connection
    try:
        esp = serial.Serial(utils.PORT_COM, 115200, timeout=0.1, write_timeout=0)
        time.sleep(2 if hunting_mode == "MANUAL" else 6)
        if esp and not utils.TEST_MODE:
            esp.write(b'F')
            time.sleep(0.5)
    except Exception as e:
        print(f"[ERROR] PORT ERROR: {e}")
        esp = None

    # Attempt capture device connection
    capture_device = None
    if not utils.TEST_MODE:
        if utils.current_system == "Windows":
            capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            capture_device = cv2.VideoCapture(0)
        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        capture_device.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    else:
        if utils.TEST_IS_VIDEO:
            capture_device = cv2.VideoCapture(utils.TEST_VIDEO_PATH)

    # Route to the appropriate hunting script
    if hunting_mode == "MANUAL":
        manual.run(capture_device, esp)
    elif hunting_mode == "GIFT":
        hunt_gift.run(capture_device, esp, encounters, shiny_found)
    elif hunting_mode == "WILD":
        hunt_wild.run(capture_device, esp, encounters, shiny_found)
    elif hunting_mode == "FISH":
        hunt_fish.run(capture_device, esp, encounters, shiny_found)

    # Cleanup hardware resources on exit
    if capture_device:
        capture_device.release()
    if esp:
        if not utils.TEST_MODE:
            esp.write(b'F')
        esp.close()

    cv2.destroyAllWindows()
    cv2.waitKey(1)


def main():
    """Main CLI Menu."""
    while True:
        status_text = "On" if utils.TEST_MODE else "Off"
        print("\n-=- Welcome to Shiny Catcher by phiphi -=-")
        print(f"[TEST MODE - {status_text}] - type \"test\"")
        print("1. Start Gift Hunting")
        print("2. Start Wild Hunting")
        print("3. Start Fish Hunting")
        print("4. Manual Control Mode")
        print("5. Exit")

        choice = input("Choose: ").strip().lower()

        if choice == 'test':
            utils.TEST_MODE = not utils.TEST_MODE
        elif choice == '1':
            start_engine("GIFT")
        elif choice == '2':
            start_engine("WILD")
        elif choice == '3':
            start_engine("FISH")
        elif choice == '4':
            start_engine("MANUAL")
        elif choice == '5' or choice == 'exit':
            sys.exit()


if __name__ == "__main__":
    main()