import sys
import os
import serial
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QFrame, QPushButton, QStackedWidget)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import utils
from hunting.manual import ManualController
from page_main import MainPage
from page_history import HistoryPage
from page_settings import SettingsPage
from config_manager import ConfigManager
from video_thread import VideoThread
from hunting_thread import HuntingThread


class ShinyCatcherGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Shiny Catcher Dashboard")
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        icon_path = os.path.join(ROOT_DIR, "pokemon_sprites", "ruby-sapphire", "shiny", "214.png")
        self.setWindowIcon(QIcon(icon_path))

        self.cfg_manager = ConfigManager()
        self._load_keybinds()
        self._init_hardware()

        # Maszyna Stanów
        self.hunt_state = "MANUAL"  # Możliwe: MANUAL, ARMED, RUNNING
        self.selected_mode = "Manual"
        self.hunting_thread = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        self._setup_navbar()

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.page_main = MainPage()
        self.page_history = HistoryPage()
        self.page_settings = SettingsPage()

        self.stacked_widget.addWidget(self.page_main)
        self.stacked_widget.addWidget(self.page_history)
        self.stacked_widget.addWidget(self.page_settings)

        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        self._connect_mode_signals()

    def _init_hardware(self):
        self.esp = None
        try:
            self.esp = serial.Serial(utils.PORT_COM, 115200, timeout=0.1, write_timeout=0)
            time.sleep(2)
            print(f"[INFO] Connected to ESP32 on {utils.PORT_COM}")
        except Exception as e:
            print(f"[WARNING] Could not connect to ESP32: {e}")
            self.esp = None

        self.manual_ctrl = ManualController(self.esp)

    def _load_keybinds(self):
        self.keybinds = {
            self.cfg_manager.get_qt_key("move_up"): 'U',
            self.cfg_manager.get_qt_key("move_down"): 'D',
            self.cfg_manager.get_qt_key("move_left"): 'L',
            self.cfg_manager.get_qt_key("move_right"): 'R',
            self.cfg_manager.get_qt_key("btn_x"): 'X',
            self.cfg_manager.get_qt_key("btn_y"): 'Y',
            self.cfg_manager.get_qt_key("btn_b"): 'B',
            self.cfg_manager.get_qt_key("btn_a"): 'A',
            self.cfg_manager.get_qt_key("btn_start"): 'S',
            self.cfg_manager.get_qt_key("btn_home"): 'H'
        }

    def _setup_navbar(self):
        self.navbar_frame = QFrame()
        self.navbar_frame.setFixedWidth(70)
        self.navbar_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 10px; }")
        self.navbar_layout = QVBoxLayout(self.navbar_frame)
        self.navbar_layout.setContentsMargins(10, 20, 10, 20)
        self.navbar_layout.setSpacing(15)

        self.btn_main = QPushButton("M")
        self.btn_history = QPushButton("H")
        self.btn_settings = QPushButton("S")

        for btn in [self.btn_main, self.btn_history, self.btn_settings]:
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("""
                QPushButton { background-color: #4a4a4a; border-radius: 10px; font-weight: bold; font-size: 18px; }
                QPushButton:hover { background-color: #5a5a5a; }
            """)
            self.navbar_layout.addWidget(btn)

        self.btn_main.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_history.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        self.navbar_layout.addStretch()
        self.main_layout.addWidget(self.navbar_frame)

    def _connect_mode_signals(self):
        """Nasłuchiwanie na zmianę trybów w GUI i aktualizacja stanu maszyny"""
        self.page_main.radio_manual.toggled.connect(lambda c: self._change_hunt_mode("Manual") if c else None)
        self.page_main.radio_gift.toggled.connect(lambda c: self._change_hunt_mode("GIFT") if c else None)
        self.page_main.radio_fish.toggled.connect(lambda c: self._change_hunt_mode("FISH") if c else None)
        self.page_main.radio_wild.toggled.connect(lambda c: self._change_hunt_mode("WILD") if c else None)

    def _change_hunt_mode(self, mode):
        if self.hunt_state == "RUNNING":
            print("[WARNING] Cannot change mode while hunting is in progress!")
            return

        self.selected_mode = mode
        if mode == "Manual":
            self.hunt_state = "MANUAL"
            self.page_main.lbl_status.setText("  MANUAL")
        else:
            self.hunt_state = "ARMED"
            # Shortened text to fit the UI panel
            self.page_main.lbl_status.setText("  READY (KEY)")

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if self.hunt_state == "RUNNING" and event.key() == Qt.Key.Key_Q:
            print("[INFO] Stop key pressed. Stopping hunt...")
            if self.hunting_thread:
                self.hunting_thread.stop()
            return

        if self.hunt_state == "ARMED":
            self._start_hunt()
            return

        if self.hunt_state == "MANUAL":
            key = event.key()
            if key in self.keybinds:
                self.manual_ctrl.send_command(self.keybinds[key])

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat() or self.hunt_state != "MANUAL":
            return

        key = event.key()
        movement_keys = [
            self.cfg_manager.get_qt_key("move_up"),
            self.cfg_manager.get_qt_key("move_down"),
            self.cfg_manager.get_qt_key("move_left"),
            self.cfg_manager.get_qt_key("move_right")
        ]

        if key in movement_keys:
            self.manual_ctrl.send_command('C')

    def _start_hunt(self):
        """Releases GUI camera and starts background hunting logic."""
        print(f"[INFO] Starting Hunt: {self.selected_mode}")
        self.hunt_state = "RUNNING"
        # Shortened text to fit the UI panel
        self.page_main.lbl_status.setText("  HUNTING...")

        self.page_main.video_thread.stop()

        is_starter = self.page_main.check_starter.isChecked()
        self.hunting_thread = HuntingThread(self.selected_mode, self.esp, is_starter)

        self.hunting_thread.frame_signal.connect(self.page_main.update_video_image)
        self.hunting_thread.stats_signal.connect(self.page_main.update_stats)
        self.hunting_thread.finished_signal.connect(self._on_hunt_finished)
        self.hunting_thread.start()

    def _on_hunt_finished(self):
        """Restores GUI preview when the hunt is stopped."""
        print("[INFO] Hunt stopped. Restoring GUI preview.")
        self.hunt_state = "ARMED"
        # Shortened text to fit the UI panel
        self.page_main.lbl_status.setText("  READY (KEY)")

        self.page_main.video_thread = VideoThread()
        self.page_main.video_thread.change_pixmap_signal.connect(self.page_main.update_video_image)
        self.page_main.video_thread.start()

    def closeEvent(self, event):
        print("[INFO] Shutting down resources...")
        if self.esp and self.esp.is_open:
            self.esp.close()

        self.page_main.video_thread.stop()
        if self.hunting_thread and self.hunting_thread.isRunning():
            self.hunting_thread.terminate()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShinyCatcherGUI()
    window.show()
    sys.exit(app.exec())