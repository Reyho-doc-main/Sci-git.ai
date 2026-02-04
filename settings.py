import pygame

class UITheme:
    # Color Palette - Industrial / Terminal Aesthetic
    BG_DARK = (10, 10, 12)
    PANEL_GREY = (22, 22, 26)
    ACCENT_ORANGE = (255, 120, 0)
    TEXT_OFF_WHITE = (210, 210, 215)
    TEXT_DIM = (120, 120, 130)
    GRID_COLOR = (28, 28, 32)
    NODE_MAIN = (0, 180, 255)
    NODE_BRANCH = (0, 255, 150)

    @staticmethod
    def draw_bracket(surface, rect, color, length=12, thickness=2):
        """Draws sharp industrial corner brackets around a rect."""
        x, y, w, h = rect
        # Top Left
        pygame.draw.lines(surface, color, False, [(x, y + length), (x, y), (x + length, y)], thickness)
        # Top Right
        pygame.draw.lines(surface, color, False, [(x + w - length, y), (x + w, y), (x + w, y + length)], thickness)
        # Bottom Left
        pygame.draw.lines(surface, color, False, [(x, y + h - length), (x, y + h), (x + length, y + h)], thickness)
        # Bottom Right
        pygame.draw.lines(surface, color, False, [(x + w - length, y + h), (x + w, y + h), (x + w, y + h - length)], thickness)

    @staticmethod
    def draw_grid(surface):
        """Draws the background industrial grid."""
        width, height = surface.get_size()
        for x in range(0, width, 40):
            pygame.draw.line(surface, UITheme.GRID_COLOR, (x, 0), (x, height))
        for y in range(0, height, 40):
            pygame.draw.line(surface, UITheme.GRID_COLOR, (0, y), (width, height))

    @staticmethod
    def render_terminal_text(surface, text, pos, font, color, width_limit=400):
        """Helper to wrap text for the side panels."""
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