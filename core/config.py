# --- FILE: core/config.py ---
import json
import os
import pygame

class ConfigManager:
    def __init__(self):
        self.config_path = "config.json"
        self.defaults = {
            "theme": "LIGHT",  # Default to Scientific Light
            "hotkeys": {
                "undo": [pygame.K_z, pygame.KMOD_CTRL],
                "redo": [pygame.K_y, pygame.KMOD_CTRL],
                "save": [pygame.K_s, pygame.KMOD_CTRL],
                "search": [pygame.K_f, pygame.KMOD_CTRL],
                "analyze": [pygame.K_a, pygame.KMOD_NONE] # Single key example
            }
        }
        self.data = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            return self.defaults.copy()
        try:
            with open(self.config_path, "r") as f:
                return {**self.defaults, **json.load(f)}
        except Exception:
            return self.defaults.copy()

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_hotkey(self, action_name):
        return self.data["hotkeys"].get(action_name, [0, 0])

    def set_theme(self, theme_name):
        self.data["theme"] = theme_name
        self.save_config()

# Global Instance
cfg = ConfigManager()