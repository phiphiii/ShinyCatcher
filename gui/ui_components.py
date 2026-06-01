from PyQt6.QtWidgets import QFrame, QVBoxLayout


class SideBorderPanel(QFrame):
    """Reusable panel with colored borders."""

    def __init__(self, color_hex):
        super().__init__()

        self.setStyleSheet(f"""
            SideBorderPanel {{
                background-color: {color_hex};
                border-radius: 15px;
            }}
        """)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(15, 0, 15, 0)
        self.outer_layout.setSpacing(0)

        self.inner_frame = QFrame()
        # Explicit styles for checkboxes and radio buttons to prevent blending
        self.inner_frame.setStyleSheet("""
                    QFrame {
                        background-color: #333333;
                        border-radius: 12px;
                    }
                    QLabel {
                        background: transparent;
                        color: #ffffff;
                    }
                    QRadioButton, QCheckBox {
                        background: transparent;
                        color: #ffffff;
                        font-size: 14px;
                        spacing: 10px; /* Zwiększony odstęp tekstu od kółka */
                    }
                    /* Naprawione wskaźniki */
                    QRadioButton::indicator, QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        background-color: #4a4a4a;
                        border: 2px solid #777777;
                    }
                    QRadioButton::indicator {
                        border-radius: 10px; /* Musi być (width + border*2) / 2 */
                    }
                    QCheckBox::indicator {
                        border-radius: 4px;
                    }
                    QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                        background-color: #ffffff;
                        border: 5px solid #555555; /* Grubsza ramka daje efekt małej kropki w środku */
                    }
                    QRadioButton::indicator:hover, QCheckBox::indicator:hover {
                        border-color: #aaaaaa;
                    }
                    QCheckBox:disabled {
                        color: #777777;
                    }
                """)
        self.outer_layout.addWidget(self.inner_frame)

    def set_inner_layout(self, layout):
        self.inner_frame.setLayout(layout)