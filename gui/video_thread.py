import cv2
import os
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from gui import utils


class VideoThread(QThread):
    """Thread to handle OpenCV video capture without blocking the GUI mainloop."""
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        if utils.current_system == "Windows":
            capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            capture_device = cv2.VideoCapture(0)

        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        while self._run_flag:
            ret, frame = capture_device.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # PERFORMANCE FIX: Resize the image before sending it to the GUI thread
                # This drastically reduces CPU load and visual latency
                preview_image = cv2.resize(rgb_image, (960, 540))

                h, w, ch = preview_image.shape
                bytes_per_line = ch * w

                qt_img = QImage(preview_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()

                self.change_pixmap_signal.emit(qt_img)
            else:
                self.msleep(10)

        capture_device.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish."""
        self._run_flag = False
        self.wait()