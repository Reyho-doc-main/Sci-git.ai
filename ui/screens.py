# --- FILE: ui/screens.py ---
import pygame
import os
from settings import UITheme
from state_manager import state
from ui.layout import layout, SCREEN_CENTER_X
from ui.components import draw_loading_overlay

class RenderEngine:
    def __init__(self, screen):
        self.screen = screen
        
        # Assets
        self.font_main = pygame.font.SysFont("Consolas", 14)
        self.font_bold = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_header = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 10)
        
        # --- NEW: Image Asset Loading ---
        self.icons = {}
        try:
            if os.path.exists("image/logo.jpg"):
                logo_raw = pygame.image.load("image/logo.jpg")
                self.logo_img = pygame.transform.smoothscale(logo_raw, (400, 260))
                self.logo_img.set_colorkey(self.logo_img.get_at((0,0)))
            else:
                self.logo_img = None
        except: 
            self.logo_img = None
            print("Warning: logo.jpg not found.")

        # Load UI Icons (Collapse/Expand/Settings)
        def load_icon(path, size):
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(img, size)
                except Exception as e:
                    print(f"Failed to load icon {path}: {e}")
            else:
                print(f"Icon missing: {path}")
            return None

        self.icons['collapse'] = load_icon("image/collapse.webp", (20, 20))
        self.icons['expand'] = load_icon("image/expand.png", (20, 20))
        self.icons['settings'] = load_icon("image/setting_icon.webp", (30, 30))

    def draw_splash(self, mouse_pos):
        self.screen.fill(UITheme.BG_LOGIN)
        if self.logo_img: 
            self.screen.blit(self.logo_img, self.logo_img.get_rect(center=(SCREEN_CENTER_X, 230)))
        
        if not state.show_login_box:
            for b in [layout.btn_new, layout.btn_load, layout.btn_import]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_main)
            
            # Note: Clear Cache button removed from here, moved to Settings
            
        else:
            box_rect = pygame.Rect(SCREEN_CENTER_X - 225, 380, 450, 240)
            pygame.draw.rect(self.screen, (20, 20, 35), box_rect, border_radius=10)
            UITheme.draw_bracket(self.screen, box_rect, UITheme.ACCENT_ORANGE)
            
            self.screen.blit(self.font_bold.render("RESEARCHER IDENTITY", True, (255, 255, 255)), (SCREEN_CENTER_X - 100, 410))
            
            input_rect = pygame.Rect(SCREEN_CENTER_X - 190, 450, 380, 45)
            pygame.draw.rect(self.screen, (10, 10, 20), input_rect)
            pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, input_rect, 2)
            
            # Draw Text Input
            txt = state.researcher_name + "|"
            self.screen.blit(self.font_bold.render(txt, True, (255, 255, 255)), (input_rect.x + 10, input_rect.y + 12))
            
            layout.btn_confirm.check_hover(mouse_pos)
            layout.btn_confirm.draw(self.screen, self.font_main)

    def draw_onboarding(self, mouse_pos):
        self.screen.fill(UITheme.BG_DARK)
        UITheme.draw_grid(self.screen)
        
        # --- Logo panel container (smaller + higher) ---
        panel_w, panel_h = 560, 260
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (SCREEN_CENTER_X, 175)

        # Use same blue tone as logo background
        logo_blue = (17, 70, 150)  # tweak if needed
        pygame.draw.rect(self.screen, logo_blue, panel, border_radius=12)
        pygame.draw.rect(self.screen, UITheme.GRID_COLOR, panel, 1, border_radius=12)
        UITheme.draw_bracket(self.screen, panel, UITheme.ACCENT_ORANGE)

        # Optional tint to soften strong logo bg (safe, does NOT change image file)
        tint = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        tint.fill((0, 0, 0, 30))  # try 20~40
        self.screen.blit(tint, panel.topleft)

        if self.logo_img:
            old_clip = self.screen.get_clip()
            self.screen.set_clip(panel)  # prevent overflow outside panel
            self.screen.blit(self.logo_img, self.logo_img.get_rect(center=panel.center))
            self.screen.set_clip(old_clip)
            
        msg1 = self.font_header.render("WELCOME TO THE LAB", True, UITheme.TEXT_OFF_WHITE)
        msg2 = self.font_bold.render("To begin, please upload your first experimental CSV file.", True, UITheme.TEXT_DIM)
        
        self.screen.blit(msg1, (SCREEN_CENTER_X - msg1.get_width()//2, 320))
        self.screen.blit(msg2, (SCREEN_CENTER_X - msg2.get_width()//2, 370))
        
        for b in [layout.btn_onboard_upload, layout.btn_skip_onboarding]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_main)

    def draw_editor(self, mouse_pos):
        self.screen.fill((10, 10, 12))
        UITheme.draw_grid(self.screen)
        
        # Header
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, (0, 0, 1280, 60))
        filename = os.path.basename(state.editor_file_path) if state.editor_file_path else "Unknown"
        self.screen.blit(self.font_bold.render(f"EDITING: {filename}", True, UITheme.ACCENT_ORANGE), (20, 20))
        self.screen.blit(self.font_main.render("Arrow Keys to Navigate | Enter to Confirm | Save to Commit", True, UITheme.TEXT_DIM), (500, 22))

        # Spreadsheet Logic
        start_x, start_y = 50, 100
        cell_w, cell_h = 100, 30
        
        if state.editor_df is not None:
            # Draw Columns
            cols = state.editor_df.columns
            for c_idx, col_name in enumerate(cols):
                cx = start_x + (c_idx * cell_w)
                if cx > 1200: break
                pygame.draw.rect(self.screen, (40, 40, 50), (cx, start_y - 30, cell_w, 30))
                pygame.draw.rect(self.screen, (80, 80, 80), (cx, start_y - 30, cell_w, 30), 1)
                self.screen.blit(self.font_small.render(col_name[:12], True, (255, 255, 255)), (cx + 5, start_y - 25))

            # Draw Rows
            row_limit = 15
            visible_df = state.editor_df.iloc[int(state.editor_scroll_y):int(state.editor_scroll_y)+row_limit]
            
            for r_idx, (idx, row) in enumerate(visible_df.iterrows()):
                actual_row_idx = int(state.editor_scroll_y) + r_idx
                ry = start_y + (r_idx * cell_h)
                
                # Row Number
                self.screen.blit(self.font_small.render(str(actual_row_idx), True, UITheme.TEXT_DIM), (10, ry + 8))
                
                for c_idx, val in enumerate(row):
                    cx = start_x + (c_idx * cell_w)
                    if cx > 1200: break
                    
                    rect = pygame.Rect(cx, ry, cell_w, cell_h)
                    is_selected = state.editor_selected_cell == (actual_row_idx, c_idx)
                    
                    bg_col = (0, 60, 100) if is_selected else (20, 20, 25)
                    pygame.draw.rect(self.screen, bg_col, rect)
                    pygame.draw.rect(self.screen, (50, 50, 60), rect, 1)
                    
                    display_val = state.editor_input_buffer if is_selected else str(val)
                    self.screen.blit(self.font_main.render(display_val[:12], True, (255, 255, 255)), (cx + 5, ry + 5))
                    
                    if is_selected:
                        pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, rect, 2)

        for b in [layout.btn_editor_save, layout.btn_editor_exit]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_bold)

    def draw_ai_loading(self, mouse_pos):
        """Draws the high-tech AI prompting screen."""
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 245))
        self.screen.blit(overlay, (0,0))
        
        UITheme.draw_scanning_lines(self.screen, pygame.time.get_ticks() // 20)
        
        l1 = self.font_header.render("ESTABLISHING NEURAL LINK...", True, UITheme.ACCENT_ORANGE)
        l2 = self.font_bold.render("TRANSMITTING EXPERIMENTAL DATA TO AZURE CLOUD", True, UITheme.TEXT_DIM)
        
        self.screen.blit(l1, (SCREEN_CENTER_X - l1.get_width()//2, 300))
        self.screen.blit(l2, (SCREEN_CENTER_X - l2.get_width()//2, 350))
        
        layout.btn_ai_stop.check_hover(mouse_pos)
        layout.btn_ai_stop.draw(self.screen, self.font_bold)

    def draw_ai_popup(self, mouse_pos):
        """Draws the AI Analysis Result Popup."""
        # Dim background
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        if UITheme.BG_DARK[0] < 50:  # Dark Mode
            overlay.fill((0, 0, 0, 200))
        else:  # Light Mode
            overlay.fill((255, 255, 255, 120))
        self.screen.blit(overlay, (0,0))
        
        # Popup Box
        w, h = 850, 560
        x, y = (1280 - w)//2, (720 - h)//2
        rect = pygame.Rect(x, y, w, h)
        
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, rect)
        pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, rect, 2)
        UITheme.draw_bracket(self.screen, rect, UITheme.ACCENT_ORANGE)
        
        # Header
        self.screen.blit(self.font_header.render("AI ANALYSIS REPORT", True, UITheme.TEXT_OFF_WHITE), (x + 20, y + 20))
        
        # Content area (scrollable style if you want later)
        content_x = x + 40
        content_y = y + 95
        content_w = w - 80
        content_h = h - 190  # leave space for buttons

        content_rect = pygame.Rect(content_x, content_y, content_w, content_h)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, content_rect, border_radius=6)
        pygame.draw.rect(self.screen, UITheme.GRID_COLOR, content_rect, 1, border_radius=6)
        pad = 14
        inner_rect = content_rect.inflate(-pad*2, -pad*2)
        text_x = inner_rect.x + 10
        wrap_w = inner_rect.w - 20   # 10px left + 10px right padding
        self.screen.set_clip(inner_rect)

        # --- SCROLL STATE ---
        if not hasattr(state, "ai_popup_scroll_y"):
            state.ai_popup_scroll_y = 0

        scroll_y = state.ai_popup_scroll_y

        # Start cursor with scroll offset applied
        y_cursor = inner_rect.y - scroll_y
        content_start_y = inner_rect.y

        data = state.ai_popup_data or {}

        # --- SUMMARY ---
        summary = data.get("summary", "No Data.")
        self.screen.blit(self.font_bold.render("SUMMARY", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
        y_cursor += 34
        y_cursor += UITheme.render_terminal_text(
            self.screen,
            summary,
            (text_x , y_cursor),
            self.font_main,
            UITheme.TEXT_OFF_WHITE,
            wrap_w
        ) + 12

        # --- ANOMALIES ---
        anomalies = data.get("anomalies", []) or []
        if anomalies:
            self.screen.blit(self.font_bold.render("DETECTED ANOMALIES", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
            y_cursor += 34

            for idx, item in enumerate(anomalies, start=1):
                line = f"{idx}. {item}"
                y_cursor += UITheme.render_terminal_text(
                    self.screen,
                    line,
                    (text_x, y_cursor),
                    self.font_main,
                    (255, 120, 120),
                    wrap_w
                ) + 6

            y_cursor += 8

        # --- NEXT STEPS ---
        next_steps = data.get("next_steps", "")
        if next_steps:
            self.screen.blit(self.font_bold.render("NEXT STEPS", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
            y_cursor += 34
            y_cursor += UITheme.render_terminal_text(
                self.screen,
                next_steps,
                (text_x, y_cursor),
                self.font_main,
                UITheme.TEXT_OFF_WHITE,
                wrap_w
            ) + 10

        # --- CLAMP SCROLL ---
        # y_cursor currently includes "-scroll_y", so convert to total content height
        content_end_y_no_scroll = y_cursor + scroll_y
        total_content_h = content_end_y_no_scroll - content_start_y

        max_scroll = max(0, int(total_content_h - inner_rect.h + 20))
        state.ai_popup_scroll_y = max(0, min(state.ai_popup_scroll_y, max_scroll))

        self.screen.set_clip(None)

        # Buttons
        layout.btn_popup_close.check_hover(mouse_pos)
        layout.btn_popup_close.draw(self.screen, self.font_bold)
        
        layout.btn_popup_download.check_hover(mouse_pos)
        layout.btn_popup_download.draw(self.screen, self.font_bold)

    def draw_plot_tooltip(self, mouse_pos):
        """Draws coordinates when hovering over the plot."""
        rel_x = (mouse_pos[0] - 850) / 400.0
        rel_x = max(0, min(1, rel_x)) 
        ctx = state.plot_context
        df = ctx.get('df')
        if df is not None and not df.empty:
            idx = int(rel_x * (len(df) - 1))
            row = df.iloc[idx]
            x_val = row[ctx['x_col']] if ctx.get('x_col') else idx
            y_val = row[ctx['y_col']] if ctx.get('y_col') else "N/A"
            tt_text = f"X: {x_val} | Y: {y_val}"
            tt_surf = self.font_small.render(tt_text, True, (255, 255, 255))
            tt_bg = pygame.Rect(mouse_pos[0] + 10, mouse_pos[1] + 10, tt_surf.get_width() + 10, 20)
            pygame.draw.rect(self.screen, (20, 20, 25), tt_bg)
            pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, tt_bg, 1)
            self.screen.blit(tt_surf, (tt_bg.x + 5, tt_bg.y + 3))

    def draw_metadata_editor(self, mouse_pos):
        """Draws the right-side panel when editing notes."""
        panel_rect = pygame.Rect(840, 420, 420, 200)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, panel_rect)
        UITheme.draw_bracket(self.screen, panel_rect, UITheme.ACCENT_ORANGE)

        # Header
        self.screen.blit(self.font_bold.render("EDITING NOTES:", True, UITheme.TEXT_DIM), (860, 430))

        # Text Area (Simple rendering of the current buffer)
        display_text = state.meta_input_notes + ("|" if (pygame.time.get_ticks() // 500) % 2 == 0 else "")
        
        UITheme.render_terminal_text(self.screen, display_text, (860, 460), self.font_main, UITheme.TEXT_OFF_WHITE, 370)

        # Save Button
        layout.btn_save_meta.check_hover(mouse_pos)
        layout.btn_save_meta.draw(self.screen, self.font_bold)

    def draw_dashboard(self, mouse_pos, tree_ui, ai_engine):
        self.screen.fill(UITheme.BG_DARK)
        UITheme.draw_grid(self.screen)
                
        # HEADER
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, (0, 0, 1280, 70))
        pygame.draw.line(self.screen, UITheme.ACCENT_ORANGE, (0, 70), (1280, 70), 2)
        proj_name = os.path.basename(state.selected_project_path).upper() if state.selected_project_path else "NO PROJECT"
        header_txt = f"SCI-GIT // {proj_name} // {state.researcher_name.upper()}"
        self.screen.blit(self.font_bold.render(header_txt, True, UITheme.ACCENT_ORANGE), (20, 10))
        
        # MENU BAR
        for b in [layout.btn_menu_file, layout.btn_menu_edit, layout.btn_menu_ai]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_small)

        # NEW: HOME button
        layout.btn_home.check_hover(mouse_pos)
        layout.btn_home.draw(self.screen, self.font_small)

        # --- DROPDOWNS ---
        
        # Helper to draw a dropdown box
        def draw_dropdown_bg(rect):
            pygame.draw.rect(self.screen, UITheme.BG_DARK, rect)
            pygame.draw.rect(self.screen, UITheme.GRID_COLOR, rect, 1)

        # FILE DROPDOWN
        if state.show_file_dropdown:
            draw_dropdown_bg(pygame.Rect(20, 66, 140, 26))
            layout.dd_file_export.check_hover(mouse_pos)
            layout.dd_file_export.draw(self.screen, self.font_small)

        # EDIT DROPDOWN
        if state.show_edit_dropdown:
            draw_dropdown_bg(pygame.Rect(90, 66, 110, 78)) # Height covers 3 buttons
            for b in [layout.dd_edit_undo, layout.dd_edit_redo, layout.dd_edit_file]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_small)

        # AI DROPDOWN
        if state.show_ai_dropdown:
            draw_dropdown_bg(pygame.Rect(160, 66, 140, 26))
            layout.dd_ai_analyze.check_hover(mouse_pos)
            layout.dd_ai_analyze.draw(self.screen, self.font_small)

        # SEARCH BAR (theme-aware)
        search_rect = pygame.Rect(850, 45, 200, 20)
        # If LIGHT theme, use a light input bg. If DARK, use darker input bg.
        is_light = UITheme.BG_DARK[0] > 150  # crude but works with your theme palette
        input_bg = UITheme.PANEL_GREY if is_light else UITheme.BG_DARK
        pygame.draw.rect(self.screen, input_bg, search_rect)
        border_col = UITheme.ACCENT_ORANGE if state.search_active else UITheme.TEXT_DIM
        pygame.draw.rect(self.screen, border_col, search_rect, 1)
        self.screen.blit(self.font_small.render("SEARCH:", True, UITheme.TEXT_DIM), (800, 48))

        display_text = state.search_text
        if state.search_active and (pygame.time.get_ticks() % 1000) > 500:
            display_text += "_"

        text_surf = self.font_small.render(display_text, True, UITheme.TEXT_OFF_WHITE)
        if text_surf.get_width() > 190:
            display_text = "..." + state.search_text[-20:]
            if state.search_active and (pygame.time.get_ticks() % 1000) > 500:
                display_text += "_"
            text_surf = self.font_small.render(display_text, True, UITheme.TEXT_OFF_WHITE)

        self.screen.blit(text_surf, (855, 48))

        # AI STATUS
        ai_status = "AI ONLINE" if ai_engine.client else "AI OFFLINE"
        ai_col = (0, 255, 150) if ai_engine.client else (200, 50, 50)
        self.screen.blit(self.font_main.render(ai_status, True, ai_col), (1150, 10))
        self.screen.blit(self.font_main.render(f"> {state.status_msg}", True, UITheme.TEXT_DIM), (850, 15))

        # TREE SURFACE
        tree_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        if pygame.mouse.get_pressed()[0] and not state.show_ai_popup: # Disable drag if popup is open
            tree_ui.update_drag(mouse_pos, (20, 80, 800, 600))
        else:
            tree_ui.dragged_node_id = None
            
        tree_ui.draw(tree_surf, mouse_pos)
        tree_ui.draw_minimap(tree_surf, tree_surf.get_rect(), self.icons)
        self.screen.blit(tree_surf, (20, 80))
        UITheme.draw_bracket(self.screen, (20, 80, 800, 600), UITheme.ACCENT_ORANGE)

        # CONTEXT ICONS ON TREE
        if len(state.selected_ids) == 1:
            for node in tree_ui.nodes:
                if node["id"] == state.selected_ids[0]:
                    pos = (node["pos"] * tree_ui.zoom_level) + tree_ui.camera_offset
                    mx, my = pos.x + 45, pos.y + 60
                    layout.btn_add_manual.rect.topleft = (mx, my)
                    layout.btn_edit_meta.rect.topleft = (mx, my + 40)
                    
                    layout.btn_add_manual.check_hover(mouse_pos)
                    layout.btn_add_manual.draw(self.screen, self.font_main)
                    layout.btn_edit_meta.check_hover(mouse_pos)
                    layout.btn_edit_meta.draw(self.screen, self.font_main)

        # RIGHT PANEL
        side_rect = (840, 80, 420, 600)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, side_rect)
        UITheme.draw_bracket(self.screen, side_rect, (100, 100, 100))

        if not state.is_editing_metadata:
            # PLOT AREA
            if state.current_plot: 
                self.screen.blit(state.current_plot, (850, 100))
                plot_rect = pygame.Rect(850, 100, 400, 300)
                pygame.draw.rect(self.screen, (50, 50, 55), plot_rect, 1)
                
                if self.icons['settings']:
                    layout.btn_axis_gear.check_hover(mouse_pos)
                    r = layout.btn_axis_gear.rect
                    self.screen.blit(self.icons['settings'], (r.x, r.y))
                    if layout.btn_axis_gear.is_hovered: pygame.draw.rect(self.screen, (255, 255, 255), r, 1)
                else:
                    layout.btn_axis_gear.check_hover(mouse_pos)
                    layout.btn_axis_gear.draw(self.screen, self.font_bold)
                
                # Fixed: Use self.draw_plot_tooltip
                if plot_rect.collidepoint(mouse_pos) and state.plot_context and not state.show_ai_popup:
                    self.draw_plot_tooltip(mouse_pos)

            # ANALYSIS TEXT
            if state.current_analysis:
                analysis_area = pygame.Rect(850, 420, 390, 200)
                self.screen.set_clip(analysis_area)
                y_pos = 420 - state.analysis_scroll_y
                summary_text = state.current_analysis.get('summary', "")
                h = UITheme.render_terminal_text(self.screen, summary_text, (855, y_pos), self.font_main, UITheme.TEXT_OFF_WHITE, 380)
                if len(state.selected_ids) == 1:
                    meta_txt = f"\nRESEARCH NOTES:\n{state.meta_input_notes}"
                    UITheme.render_terminal_text(self.screen, meta_txt, (855, y_pos + h), self.font_main, UITheme.ACCENT_ORANGE, 380)
                self.screen.set_clip(None)
        else:
            # FIXED: Implemented this method above
            self.draw_metadata_editor(mouse_pos)

        # COMMON BUTTONS
        for b in [layout.btn_export, layout.btn_branch]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_main)
        
        # OVERLAYS
        if state.is_processing:
            if state.processing_mode == "AI":
                self.draw_ai_loading(mouse_pos)
            else:
                draw_loading_overlay(self.screen, self.font_bold)
        
        if state.show_conversion_dialog:
            self.draw_conversion_dialog(mouse_pos)
            
        # --- NEW: AI POPUP OVERLAY ---
        if state.show_ai_popup:
            self.draw_ai_popup(mouse_pos)