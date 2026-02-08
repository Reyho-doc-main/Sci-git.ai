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
        
        try:
            logo_raw = pygame.image.load("logo.jpg")
            self.logo_img = pygame.transform.smoothscale(logo_raw, (400, 300))
            self.logo_img.set_colorkey(self.logo_img.get_at((0,0)))
        except: 
            self.logo_img = None

    def draw_splash(self, mouse_pos):
        self.screen.fill(UITheme.BG_LOGIN)
        if self.logo_img: 
            self.screen.blit(self.logo_img, self.logo_img.get_rect(center=(SCREEN_CENTER_X, 230)))
        
        if not state.show_login_box:
            for b in [layout.btn_new, layout.btn_load, layout.btn_import]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_main)
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
        
        if self.logo_img: 
            self.screen.blit(self.logo_img, self.logo_img.get_rect(center=(SCREEN_CENTER_X, 200)))
            
        msg1 = self.font_header.render("WELCOME TO THE LAB", True, (255, 255, 255))
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
        self.screen.blit(self.font_main.render("Use Arrow Keys to Scroll | Enter to Confirm Cell | Save to Commit", True, UITheme.TEXT_DIM), (500, 22))

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
        for b in [layout.btn_menu_file, layout.btn_menu_edit, layout.btn_menu_analyze]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_small)

        # SEARCH BAR
        search_rect = pygame.Rect(850, 45, 200, 20)
        pygame.draw.rect(self.screen, (10, 10, 15), search_rect)
        pygame.draw.rect(self.screen, (UITheme.ACCENT_ORANGE if state.search_active else (50, 50, 60)), search_rect, 1)
        self.screen.blit(self.font_small.render("SEARCH:", True, UITheme.TEXT_DIM), (800, 48))
        self.screen.blit(self.font_small.render(state.search_text + ("|" if state.search_active else ""), True, (255, 255, 255)), (855, 48))

        # AI STATUS
        ai_status = "AI ONLINE" if ai_engine.client else "AI OFFLINE"
        ai_col = (0, 255, 150) if ai_engine.client else (200, 50, 50)
        self.screen.blit(self.font_main.render(ai_status, True, ai_col), (1150, 10))
        self.screen.blit(self.font_main.render(f"> {state.status_msg}", True, UITheme.TEXT_DIM), (850, 15))

        # TREE SURFACE
        tree_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        if pygame.mouse.get_pressed()[0]:
            tree_ui.update_drag(mouse_pos, (20, 80, 800, 600))
        else:
            tree_ui.dragged_node_id = None
            
        tree_ui.draw(tree_surf, mouse_pos)
        tree_ui.draw_minimap(tree_surf, tree_surf.get_rect())
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
                
                layout.btn_axis_gear.check_hover(mouse_pos)
                layout.btn_axis_gear.draw(self.screen, self.font_bold)
                
                # Tooltip logic (Visual only)
                if plot_rect.collidepoint(mouse_pos) and state.plot_context:
                    self.draw_plot_tooltip(mouse_pos)

                # AXIS SELECTOR
                if state.show_axis_selector and state.plot_context:
                    self.draw_axis_selector(mouse_pos)

            # ANALYSIS TEXT
            if state.current_analysis:
                UITheme.render_terminal_text(self.screen, state.current_analysis.get('summary', ""), (855, 420), self.font_main, UITheme.TEXT_OFF_WHITE, 390)
                if len(state.selected_ids) == 1:
                    meta_txt = f"NOTE: {state.meta_input_notes}\nTEMP: {state.meta_input_temp} | ID: {state.meta_input_sid}"
                    if state.meta_input_notes or state.meta_input_temp:
                        UITheme.render_terminal_text(self.screen, meta_txt, (855, 550), self.font_main, UITheme.ACCENT_ORANGE, 390)
        else:
            # METADATA EDITOR
            self.draw_metadata_editor(mouse_pos)

        # COMMON BUTTONS
        for b in [layout.btn_export, layout.btn_branch, layout.btn_snapshot_export]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_main)
        
        # OVERLAYS
        if state.is_processing: 
            draw_loading_overlay(self.screen, self.font_bold)
        
        if state.show_conversion_dialog:
            self.draw_conversion_dialog(mouse_pos)

    def draw_plot_tooltip(self, mouse_pos):
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

    def draw_axis_selector(self, mouse_pos):
        axis_selector_rect = pygame.Rect(850, 130, 200, 300)
        pygame.draw.rect(self.screen, (15, 15, 20), axis_selector_rect)
        pygame.draw.rect(self.screen, (80, 80, 90), axis_selector_rect, 2)
        self.screen.blit(self.font_bold.render("AXIS SELECTION", True, UITheme.ACCENT_ORANGE), (860, 135))
        self.screen.blit(self.font_small.render("CLICK COL TO SET: [ X ]  [ Y ]", True, UITheme.TEXT_DIM), (860, 150))
        
        df = state.plot_context['df']
        numeric_cols = df.select_dtypes(include=['number']).columns
        y_off = 160
        for col in numeric_cols:
            is_x = col == state.plot_context.get('x_col')
            is_y = col == state.plot_context.get('y_col')
            col_col = (255, 255, 255)
            if is_x: col_col = (255, 120, 0)
            if is_y: col_col = (0, 255, 255)
            
            row_rect = pygame.Rect(850, y_off, 200, 25)
            if row_rect.collidepoint(mouse_pos): 
                pygame.draw.rect(self.screen, (30, 30, 40), row_rect)
            
            self.screen.blit(self.font_main.render(col[:20], True, col_col), (860, y_off + 4))
            if is_x: self.screen.blit(self.font_small.render("[X]", True, col_col), (980, y_off + 6))
            if is_y: self.screen.blit(self.font_small.render("[Y]", True, col_col), (1010, y_off + 6))
            y_off += 25

    def draw_metadata_editor(self, mouse_pos):
        self.screen.blit(self.font_bold.render("MANUAL DATA ENTRY", True, UITheme.ACCENT_ORANGE), (855, 100))
        y_ptr = 150
        for label, key in [("NOTES:", "notes"), ("TEMP (°C):", "temp"), ("SAMPLE ID:", "sid")]:
            self.screen.blit(self.font_main.render(label, True, UITheme.TEXT_DIM), (855, y_ptr))
            rect = pygame.Rect(855, y_ptr + 20, 390, 35)
            pygame.draw.rect(self.screen, (10, 10, 15), rect)
            
            is_active = state.active_field == key
            pygame.draw.rect(self.screen, (UITheme.ACCENT_ORANGE if is_active else (50, 50, 60)), rect, 1)
            
            val = state.meta_input_notes if key == "notes" else (state.meta_input_temp if key == "temp" else state.meta_input_sid)
            self.screen.blit(self.font_main.render(val + ("|" if is_active else ""), True, (255, 255, 255)), (860, y_ptr + 28))
            y_ptr += 80
        layout.btn_save_meta.check_hover(mouse_pos)
        layout.btn_save_meta.draw(self.screen, self.font_main)

    def draw_conversion_dialog(self, mouse_pos):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0,0))
        
        d_rect = pygame.Rect(440, 260, 400, 200)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, d_rect)
        UITheme.draw_bracket(self.screen, d_rect, UITheme.ACCENT_ORANGE)
        
        msg1 = self.font_bold.render("UNIT MISMATCH DETECTED", True, UITheme.ACCENT_ORANGE)
        msg2 = self.font_main.render(f"Convert Secondary Node to {state.pending_conversion[2]}?", True, UITheme.TEXT_OFF_WHITE)
        msg3 = self.font_main.render("This updates the CSV file permanently.", True, UITheme.TEXT_DIM)
        
        self.screen.blit(msg1, (d_rect.centerx - msg1.get_width()//2, 280))
        self.screen.blit(msg2, (d_rect.centerx - msg2.get_width()//2, 320))
        self.screen.blit(msg3, (d_rect.centerx - msg3.get_width()//2, 350))
        
        layout.btn_conv_yes.check_hover(mouse_pos)
        layout.btn_conv_yes.draw(self.screen, self.font_bold)
        layout.btn_conv_no.check_hover(mouse_pos)
        layout.btn_conv_no.draw(self.screen, self.font_bold)