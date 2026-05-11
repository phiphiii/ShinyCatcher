import cv2
import time
import threading
import queue
import utils


def run(capture_device, esp):
    """Executes the manual control loop."""
    print("\n-=-=-=- MANUAL CONTROL INSTRUCTIONS -=-=-=-")
    print("Type a single character command and press Enter.")
    print("  l  - Tap Left             L  - Hold Left")
    print("  r  - Tap Right            R  - Hold Right")
    print("  u  - Tap Up               U  - Hold Up")
    print("  d  - Tap Down             D  - Hold Down")
    print("  C  - Release Hold (Stop running)")
    print("  A  - Press 'A' button")
    print("  X  - Press 'X' button")
    print("  S  - Press 'Start'")
    print("  H  - Press 'Home'")
    print("  F  - Turn Off Alarm")
    print("Type 'exit' or 'quit' to return to the main menu.")
    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

    input_queue = queue.Queue()

    # Background thread to capture console input without freezing the video stream
    def read_console():
        while True:
            try:
                cmd = input("Command > ").strip()
                input_queue.put(cmd)
                if cmd.lower() in ['exit', 'quit']:
                    break
            except EOFError:
                break

    console_thread = threading.Thread(target=read_console, daemon=True)
    console_thread.start()

    valid_commands = ['l', 'r', 'u', 'd', 'L', 'R', 'U', 'D', 'C', 'A', 'X', 'S', 'H', 'F', 'Q']

    while True:
        # Keep fetching frames to keep the stream live
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

        disp_frame = current_frame.copy()

        # Clean UI: Only Status text, zero OpenCV rectangles or additional data
        cv2.putText(disp_frame, 'Status: MANUAL_MODE', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)

        resized_frame = cv2.resize(disp_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Stream', resized_frame)

        # Process queued console commands non-blockingly
        try:
            cmd = input_queue.get_nowait()
            if cmd.lower() in ['exit', 'quit']:
                print("\n[INFO] Exiting Manual Mode...\n")
                break

            # Process each character in the input string sequentially
            for char in cmd:
                if char in valid_commands:
                    if esp and not utils.TEST_MODE:
                        esp.write(char.encode())
                        print(f"  [+] Sent command: {char}")
                        # Small delay to give ESP32 time to finish its internal 100ms delay
                        time.sleep(0.15)
                    else:
                        print(f"  [TEST] Would send: {char}")
                        time.sleep(0.15)
                else:
                    # Ignore unknown characters silently, but print a warning for non-spaces
                    if char != ' ':
                        print(f"  [-] Ignored unknown character: '{char}'")

        except queue.Empty:
            pass

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Safety turn off alarm before exiting
    if esp and not utils.TEST_MODE:
        esp.write(b'F')