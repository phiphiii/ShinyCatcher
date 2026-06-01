import time
from gui import utils


class ManualController:
    """Handles manual control commands sent to the microcontroller."""

    def __init__(self, esp):
        self.esp = esp

    def send_command(self, command_char):
        """Sends a single character command to the ESP32."""
        if self.esp and not utils.TEST_MODE:
            try:
                self.esp.write(command_char.encode())
                print(f"  [+] Sent manual command: {command_char}")
                # Small delay to give ESP32 time to finish internal loops
                time.sleep(0.15)
            except Exception as e:
                print(f"[ERROR] Failed to send command: {e}")
        else:
            print(f"  [TEST] Would send manual command: {command_char}")