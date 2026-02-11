# --- START OF FILE settings.py ---
import pygame
from ui.styles import theme

# This MetaClass allows us to access properties like UITheme.BG_DARK
# and have them dynamically return the value from the current 'theme' object.
class DynamicThemeMeta(type):
    @property
    def BG_DARK(cls): return theme.BG_MAIN # Mapped to Main BG
    
    # FIXED: Hardcoded to Blue so the logo always looks good on Splash Screen
    @property
    def BG_LOGIN(cls): return (0, 67, 153) 
    
    @property
    def PANEL_GREY(cls): return theme.BG_PANEL
    @property
    def ACCENT_ORANGE(cls): return theme.ACCENT
    @property
    def TEXT_OFF_WHITE(cls): return theme.TEXT_MAIN
    @property
    def TEXT_DIM(cls): return theme.TEXT_DIM
    @property
    def GRID_COLOR(cls): return theme.GRID
    @property
    def NODE_MAIN(cls): return theme.NODE_MAIN
    @property
    def NODE_BRANCH(cls): return theme.NODE_BRANCH
    @property
    def LOGO_CYAN(cls): return theme.ACCENT_SEC

class UITheme(metaclass=DynamicThemeMeta):
    # Static methods remain, but they use the passed color or theme defaults
    @staticmethod
    def draw_bracket(surface, rect, color, length=12, thickness=2):
        theme.draw_bracket(surface, rect, color, length, thickness)

    @staticmethod
    def draw_grid(surface):
        width, height = surface.get_size()
        for x in range(0, width, 40):
            pygame.draw.line(surface, theme.GRID, (x, 0), (x, height))
        for y in range(0, height, 40):
            pygame.draw.line(surface, theme.GRID, (0, y), (width, height))

    @staticmethod
    def render_terminal_text(surface, text, pos, font, color, width_limit=400):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            if font.size(test_line)[0] > width_limit:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))

        y_offset = 0
        for line in lines:
            text_surf = font.render(line, True, color)
            surface.blit(text_surf, (pos[0], pos[1] + y_offset))
            y_offset += font.get_linesize()
        return y_offset
    
    @staticmethod
    def draw_orange_streaks(surface, frame_count):
        # Only draw streaks in Dark Mode for aesthetic
        if theme.BG_MAIN[0] < 50: 
            width, height = surface.get_size()
            y_pos = (frame_count * 2) % height
            pygame.draw.line(surface, (100, 50, 0), (0, y_pos), (width, y_pos), 1)
            pygame.draw.line(surface, theme.ACCENT, (20, 0), (20, height), 1)
            pygame.draw.line(surface, theme.ACCENT, (width-20, 0), (width-20, height), 1)

    @staticmethod
    def draw_scanning_lines(surface, frame_count):
        width, height = surface.get_size()
        y_pos = (frame_count * 2) % height
        
        # Glow effect
        scan_surf = pygame.Surface((width, 2), pygame.SRCALPHA)
        # Use Accent color for scan
        c = theme.ACCENT
        scan_surf.fill((c[0], c[1], c[2], 100)) 
        surface.blit(scan_surf, (0, y_pos))
        
        pygame.draw.line(surface, theme.ACCENT, (20, 0), (20, height), 1)
        pygame.draw.line(surface, theme.ACCENT, (width-20, 0), (width-20, height), 1)