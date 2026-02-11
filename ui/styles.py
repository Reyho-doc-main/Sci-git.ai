# ---FILE: ui/styles.py ---
import pygame
from core.config import cfg

class ThemePalette:
    def __init__(self):
        self.update_theme()

    def update_theme(self):
        mode = cfg.data.get("theme", "LIGHT")
        
        if mode == "LIGHT":
            # Scientific Journal Aesthetic
            self.BG_MAIN = (245, 247, 250)      # Off-white paper
            self.BG_PANEL = (255, 255, 255)     # Pure white
            self.BG_DARK = (230, 235, 240)      # Slight contrast
            self.TEXT_MAIN = (40, 44, 52)       # Dark Slate
            self.TEXT_DIM = (100, 110, 120)
            self.ACCENT = (0, 122, 204)         # Scientific Blue
            self.ACCENT_SEC = (255, 140, 0)     # Data Orange
            self.GRID = (220, 225, 230)
            self.NODE_MAIN = (0, 122, 204)
            self.NODE_BRANCH = (100, 180, 80)
            self.BORDER = (200, 205, 210)
        else:
            # Industrial Dark (Original)
            self.BG_MAIN = (10, 10, 12)
            self.BG_PANEL = (22, 22, 26)
            self.BG_DARK = (5, 5, 8)
            self.TEXT_MAIN = (210, 210, 215)
            self.TEXT_DIM = (120, 120, 130)
            self.ACCENT = (255, 120, 0)         # Industrial Orange
            self.ACCENT_SEC = (0, 180, 255)     # Cyan
            self.GRID = (28, 28, 32)
            self.NODE_MAIN = (0, 180, 255)
            self.NODE_BRANCH = (0, 255, 150)
            self.BORDER = (50, 50, 60)

    def draw_bracket(self, surface, rect, color, length=12, thickness=2):
        x, y, w, h = rect
        # Top Left
        pygame.draw.lines(surface, color, False, [(x, y + length), (x, y), (x + length, y)], thickness)
        # Top Right
        pygame.draw.lines(surface, color, False, [(x + w - length, y), (x + w, y), (x + w, y + length)], thickness)
        # Bottom Left
        pygame.draw.lines(surface, color, False, [(x, y + h - length), (x, y + h), (x + length, y + h)], thickness)
        # Bottom Right
        pygame.draw.lines(surface, color, False, [(x + w - length, y + h), (x + w, y + h), (x + w, y + h - length)], thickness)

theme = ThemePalette()