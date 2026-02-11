# --- File: ui/axis_and_settings.py ---
import pygame
from ui.styles import theme
from ui.components import Button
from core.config import cfg
from state_manager import state

class AxisSelector:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 220, 300)
        self.font = pygame.font.SysFont("Consolas", 12)
        self.close_btn = Button(0, 0, 20, 20, "X", (200, 50, 50))

    def draw(self, surface, x, y, context):
        self.rect.topleft = (x, y)
        
        # Background
        pygame.draw.rect(surface, theme.BG_PANEL, self.rect)
        pygame.draw.rect(surface, theme.ACCENT, self.rect, 1)
        theme.draw_bracket(surface, self.rect, theme.ACCENT)

        # Header
        header_surf = self.font.render("PLOT CONFIGURATION", True, theme.ACCENT)
        surface.blit(header_surf, (x + 10, y + 10))
        
        self.close_btn.rect.topleft = (x + 190, y + 5)
        self.close_btn.draw(surface, self.font)

        if not context or 'df' not in context:
            return

        df = context['df']
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        # Column List
        start_y = y + 40
        for i, col in enumerate(numeric_cols):
            # Row Background
            row_rect = pygame.Rect(x + 10, start_y + (i * 25), 200, 22)
            is_hover = row_rect.collidepoint(pygame.mouse.get_pos())
            
            col_color = theme.BG_DARK if not is_hover else theme.GRID
            pygame.draw.rect(surface, col_color, row_rect)
            
            # Text
            txt = self.font.render(col[:20], True, theme.TEXT_MAIN)
            surface.blit(txt, (x + 15, row_rect.y + 4))
            
            # Indicators (X or Y)
            if col == context.get('x_col'):
                pygame.draw.circle(surface, theme.ACCENT, (x + 190, row_rect.centery), 4)
                lbl = self.font.render("X", True, theme.ACCENT)
                surface.blit(lbl, (x + 175, row_rect.y + 4))
            
            if col == context.get('y_col'):
                pygame.draw.circle(surface, theme.ACCENT_SEC, (x + 190, row_rect.centery), 4)
                lbl = self.font.render("Y", True, theme.ACCENT_SEC)
                surface.blit(lbl, (x + 175, row_rect.y + 4))

    def handle_click(self, mouse_pos, context, worker_ctrl, task_manager):
        if self.close_btn.rect.collidepoint(mouse_pos):
            state.show_axis_selector = False
            return

        if not self.rect.collidepoint(mouse_pos) or not context:
            state.show_axis_selector = False
            return

        df = context['df']
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        local_y = mouse_pos[1] - (self.rect.y + 40)
        idx = local_y // 25
        
        if 0 <= idx < len(numeric_cols):
            col_name = numeric_cols[idx]
            
            # Left Click = Set Y, Right Click = Set X
            is_left_click = pygame.mouse.get_pressed()[0]
            
            new_x = context.get('x_col')
            new_y = context.get('y_col')
            
            if is_left_click:
                new_y = col_name
            else:
                new_x = col_name

            state.processing_mode = "LOCAL"
            task_manager.add_task(worker_ctrl.worker_load_experiment, 
                                  [state.selected_ids, new_x, new_y, True])


class SettingsMenu:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 400, 500)
        self.font = pygame.font.SysFont("Consolas", 14)
        self.btn_theme_light = Button(0, 0, 150, 40, "SCIENTIFIC LIGHT", (200, 200, 200))
        self.btn_theme_dark = Button(0, 0, 150, 40, "INDUSTRIAL DARK", (50, 50, 50))
        
        # NEW: Clear Cache Button
        self.btn_clear_cache = Button(0, 0, 360, 40, "CLEAR PYCACHE", (200, 50, 50))
        
        self.btn_close = Button(0, 0, 360, 40, "SAVE & CLOSE", theme.ACCENT)

    def draw(self, surface):
        cx, cy = surface.get_rect().center
        self.rect.center = (cx, cy)
        
        # Overlay Dim
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0,0))

        # Panel
        pygame.draw.rect(surface, theme.BG_PANEL, self.rect)
        pygame.draw.rect(surface, theme.ACCENT, self.rect, 2)
        
        # Content
        y_off = self.rect.y + 20
        title = self.font.render("SYSTEM CONFIGURATION", True, theme.TEXT_MAIN)
        surface.blit(title, (self.rect.x + 20, y_off))
        
        y_off += 50
        lbl_theme = self.font.render("COLOR THEME:", True, theme.TEXT_DIM)
        surface.blit(lbl_theme, (self.rect.x + 20, y_off))
        
        self.btn_theme_light.rect.topleft = (self.rect.x + 20, y_off + 25)
        self.btn_theme_dark.rect.topleft = (self.rect.x + 190, y_off + 25)
        
        self.btn_theme_light.draw(surface, self.font)
        self.btn_theme_dark.draw(surface, self.font)
        
        # Hotkeys
        y_off += 100
        lbl_keys = self.font.render("ACTIVE HOTKEYS:", True, theme.TEXT_DIM)
        surface.blit(lbl_keys, (self.rect.x + 20, y_off))
        
        y_off += 30
        for action, keys in cfg.data['hotkeys'].items():
            key_name = pygame.key.name(keys[0]).upper()
            mod = "CTRL+" if keys[1] & pygame.KMOD_CTRL else ""
            txt = f"{action.upper()}: {mod}{key_name}"
            surface.blit(self.font.render(txt, True, theme.TEXT_MAIN), (self.rect.x + 30, y_off))
            y_off += 20

        # Clear Cache Button
        self.btn_clear_cache.rect.topleft = (self.rect.x + 20, self.rect.bottom - 110)
        self.btn_clear_cache.draw(surface, self.font)

        # Close
        self.btn_close.rect.bottomleft = (self.rect.x + 20, self.rect.bottom - 20)
        self.btn_close.draw(surface, self.font)

    def handle_click(self, mouse_pos):
        if self.btn_theme_light.check_hover(mouse_pos):
            cfg.set_theme("LIGHT")
            theme.update_theme()
        elif self.btn_theme_dark.check_hover(mouse_pos):
            cfg.set_theme("DARK")
            theme.update_theme()
        elif self.btn_clear_cache.check_hover(mouse_pos):
            return "CLEAR_CACHE"
        elif self.btn_close.check_hover(mouse_pos):
            state.show_settings = False
        return None