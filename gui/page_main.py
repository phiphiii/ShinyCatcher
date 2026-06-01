from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QRadioButton, QCheckBox, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui_components import SideBorderPanel
from video_thread import VideoThread


class MainPage(QWidget):
    """Main dashboard containing video feed and control panels."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

        # Start the video feed thread
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_video_image)
        self.video_thread.start()

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)

        # Left area: Video Feed
        self.video_label = QLabel("OpenCV Video Feed Placeholder\n(Nintendo Switch Stream)")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 10px;
                font-size: 24px;
                color: #777777;
            }
        """)
        self.main_layout.addWidget(self.video_label)

        # Right area: Container for panels
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)

        # Panel 1: Red (Stats)
        panel1 = SideBorderPanel("#FF3B30")
        layout1 = QVBoxLayout()
        layout1.setContentsMargins(20, 15, 20, 15)
        layout1.addWidget(self._create_bold_label("Encounters:"))
        self.lbl_encounters = self._create_value_label("  0")
        layout1.addWidget(self.lbl_encounters)
        layout1.addWidget(self._create_bold_label("Shiny Found:"))
        self.lbl_shiny_found = self._create_value_label("  0")
        layout1.addWidget(self.lbl_shiny_found)
        layout1.addStretch()
        panel1.set_inner_layout(layout1)
        self.right_layout.addWidget(panel1)

        # Panel 2: Blue (Hunting Status)
        panel2 = SideBorderPanel("#0A84FF")
        layout2 = QVBoxLayout()
        layout2.setContentsMargins(20, 15, 20, 15)
        layout2.addWidget(self._create_bold_label("Hunting mode:"))
        self.lbl_current_mode = self._create_value_label("  Fishing")
        layout2.addWidget(self.lbl_current_mode)

        layout2.addWidget(self._create_bold_label("Current status:"))
        self.lbl_status = self._create_value_label("  MANUAL CONTROL")
        layout2.addWidget(self.lbl_status)

        layout2.addWidget(self._create_bold_label("Wait time:"))
        self.lbl_wait_time = self._create_value_label("  - ")
        layout2.addWidget(self.lbl_wait_time)

        layout2.addWidget(self._create_bold_label("Yellow Px:"))
        self.lbl_yellow_px = self._create_value_label("  0")
        layout2.addWidget(self.lbl_yellow_px)
        layout2.addStretch()
        panel2.set_inner_layout(layout2)
        self.right_layout.addWidget(panel2)

        # Panel 3: Yellow (Controls)
        panel3 = SideBorderPanel("#FFD60A")
        layout3 = QGridLayout()
        layout3.setContentsMargins(20, 15, 20, 15)
        layout3.addWidget(self._create_bold_label("Hunting mode:"), 0, 0, 1, 2)

        self.radio_manual = QRadioButton("Manual")
        self.radio_gift = QRadioButton("Gift")
        self.radio_fish = QRadioButton("Fish")
        self.radio_wild = QRadioButton("Wild")
        self.check_starter = QCheckBox("Starter")

        # FOCUS FIX: Prevent keyboard inputs from switching radio buttons
        for widget in [self.radio_manual, self.radio_gift, self.radio_fish, self.radio_wild, self.check_starter]:
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout3.addWidget(self.radio_manual, 1, 0)
        layout3.addWidget(self.radio_gift, 2, 0)
        layout3.addWidget(self.check_starter, 2, 1)
        layout3.addWidget(self.radio_fish, 3, 0)
        layout3.addWidget(self.radio_wild, 4, 0)

        self.radio_fish.setChecked(True)
        self.check_starter.setEnabled(False)

        panel3.set_inner_layout(layout3)
        self.right_layout.addWidget(panel3)

        # Panel 4: Purple (Empty/Extra)
        panel4 = SideBorderPanel("#BF5AF2")
        self.right_layout.addWidget(panel4)

        self.right_layout.setStretch(0, 8)
        self.right_layout.setStretch(1, 14)
        self.right_layout.setStretch(2, 10)
        self.right_layout.setStretch(3, 19)

        self.main_layout.addWidget(self.right_container)
        self.main_layout.setStretch(0, 24)
        self.main_layout.setStretch(1, 5)

    def _create_bold_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; font-size: 16px;")
        return label

    def _create_value_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 16px; color: #cccccc;")
        return label

    def _connect_signals(self):
        self.radio_gift.toggled.connect(self._on_gift_toggled)

        # Sync Blue Panel label when a mode is selected
        self.radio_manual.toggled.connect(lambda checked: self._update_mode_label("Manual") if checked else None)
        self.radio_gift.toggled.connect(lambda checked: self._update_mode_label("Gift") if checked else None)
        self.radio_fish.toggled.connect(lambda checked: self._update_mode_label("Fishing") if checked else None)
        self.radio_wild.toggled.connect(lambda checked: self._update_mode_label("Wild") if checked else None)

    def _on_gift_toggled(self, is_checked):
        self.check_starter.setEnabled(is_checked)
        if not is_checked:
            self.check_starter.setChecked(False)

    def _update_mode_label(self, mode_name):
        """Updates the text inside the Blue Panel."""
        self.lbl_current_mode.setText(f"  {mode_name}")

    def update_video_image(self, qt_img):
        """Updates the video label with the new frame from the VideoThread."""
        # Using FastTransformation for maximum performance
        scaled_img = qt_img.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.FastTransformation)
        self.video_label.setPixmap(QPixmap.fromImage(scaled_img))

    def update_stats(self, data):
        """Updates the GUI labels dynamically based on background thread data."""
        if 'status' in data:
            self.lbl_status.setText(f"  {data['status']}")
        if 'wait_time' in data:
            self.lbl_wait_time.setText(f"  {data['wait_time']}")
        if 'encounters' in data:
            self.lbl_encounters.setText(f"  {data['encounters']}")
        if 'shiny_found' in data:
            self.lbl_shiny_found.setText(f"  {data['shiny_found']}")