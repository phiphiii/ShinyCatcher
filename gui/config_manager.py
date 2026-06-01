import json
import os
from PyQt6.QtCore import Qt

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "keybinds": {
        "move_up": "W",
        "move_down": "S",
        "move_left": "A",
        "move_right": "D",
        "btn_x": "I",
        "btn_y": "J",
        "btn_b": "K",
        "btn_a": "L",
        "btn_start": "Q",
        "btn_home": "H"
    }
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_CONFIG

    def save_config(self, data=None):
        if data is not None:
            self.config = data
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_qt_key(self, action_name):
        key_str = self.config["keybinds"].get(action_name, "")

        special_keys = {
            "Up": Qt.Key.Key_Up,
            "Down": Qt.Key.Key_Down,
            "Left": Qt.Key.Key_Left,
            "Right": Qt.Key.Key_Right
        }

        if key_str in special_keys:
            return special_keys[key_str]

        return getattr(Qt.Key, f"Key_{key_str.upper()}", None)