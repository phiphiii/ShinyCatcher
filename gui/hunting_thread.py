import cv2
import os
import sys
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QThread, pyqtSignal

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from gui import utils
from hunting import hunt_gift, hunt_fish, hunt_wild


class HuntingThread(QThread):
    finished_signal = pyqtSignal()
    frame_signal = pyqtSignal(QImage)
    stats_signal = pyqtSignal(dict)  # New signal to transport UI stats safely

    def __init__(self, mode, esp, is_starter=False):
        super().__init__()
        self.mode = mode
        self.esp = esp
        self.is_starter = is_starter

    def frame_callback(self, frame, mask=None, ui_kwargs=None):
        """Converts frame for GUI and emits stats dictionary."""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        preview = cv2.resize(rgb_image, (960, 540))
        h, w, ch = preview.shape
        bytes_per_line = ch * w
        qt_img = QImage(preview.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()

        self.frame_signal.emit(qt_img)

        # Emit the dictionary with UI updates if provided
        if ui_kwargs:
            self.stats_signal.emit(ui_kwargs)

    def run(self):
        utils.STOP_FLAG = False
        utils.FRAME_CALLBACK = self.frame_callback

        encounters, shiny_found = utils.load_counter()

        if utils.current_system == "Windows":
            capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            capture_device = cv2.VideoCapture(0)

        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        if self.mode == "GIFT":
            hunt_gift.run(capture_device, self.esp, encounters, shiny_found, self.is_starter)
        elif self.mode == "FISH":
            hunt_fish.run(capture_device, self.esp, encounters, shiny_found)
        elif self.mode == "WILD":
            hunt_wild.run(capture_device, self.esp, encounters, shiny_found)

        capture_device.release()
        utils.FRAME_CALLBACK = None
        self.finished_signal.emit()

    def stop(self):
        """Safely interrupts the hunting loop."""
        utils.STOP_FLAG = True
        self.wait()