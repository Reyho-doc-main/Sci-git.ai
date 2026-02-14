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
        self.font_main = pygame.font.SysFont("Consolas", 14)
        self.font_bold = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_header = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 10)
        
        self.icons = {}
        try:
            if os.path.exists("image/logo.jpg"):
                logo_raw = pygame.image.load("image/logo.jpg")
                self.logo_img = pygame.transform.smoothscale(logo_raw, (400, 260))
                self.logo_img.set_colorkey(self.logo_img.get_at((0,0)))
            else: self.logo_img = None
        except: self.logo_img = None

        def load_icon(path, size):
            if os.path.exists(path):
                try: return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), size)
                except: return None
            return None

        self.icons['collapse'] = load_icon("image/collapse.webp", (20, 20))
        self.icons['expand'] = load_icon("image/expand.png", (20, 20))
        self.icons['settings'] = load_icon("image/setting_icon.webp", (30, 30))
        self.icons['graph'] = load_icon("image/graph.png", (30, 30))

    # ... [draw_splash, draw_onboarding, draw_editor, draw_ai_loading, draw_ai_popup, draw_api_config_modal, draw_plot_tooltip, draw_metadata_editor, draw_delete_confirm_modal remain unchanged] ...
    
    def draw_splash(self, mouse_pos):
        self.screen.fill(UITheme.BG_LOGIN)
        if self.logo_img: self.screen.blit(self.logo_img, self.logo_img.get_rect(center=(SCREEN_CENTER_X, 230)))
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
            txt = state.researcher_name + "|"
            self.screen.blit(self.font_bold.render(txt, True, (255, 255, 255)), (input_rect.x + 10, input_rect.y + 12))
            layout.btn_confirm.check_hover(mouse_pos)
            layout.btn_confirm.draw(self.screen, self.font_main)

    def draw_onboarding(self, mouse_pos):
        self.screen.fill(UITheme.BG_DARK)
        UITheme.draw_grid(self.screen)
        panel_w, panel_h = 560, 260
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (SCREEN_CENTER_X, 175)
        logo_blue = (17, 70, 150)
        pygame.draw.rect(self.screen, logo_blue, panel, border_radius=12)
        pygame.draw.rect(self.screen, UITheme.GRID_COLOR, panel, 1, border_radius=12)
        UITheme.draw_bracket(self.screen, panel, UITheme.ACCENT_ORANGE)
        tint = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        tint.fill((0, 0, 0, 30))
        self.screen.blit(tint, panel.topleft)
        if self.logo_img:
            old_clip = self.screen.get_clip()
            self.screen.set_clip(panel)
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
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, (0, 0, 1280, 60))
        filename = os.path.basename(state.editor_file_path) if state.editor_file_path else "Unknown"
        self.screen.blit(self.font_bold.render(f"EDITING: {filename}", True, UITheme.ACCENT_ORANGE), (20, 20))
        self.screen.blit(self.font_main.render("Arrow Keys to Navigate | Enter to Confirm | Save to Commit", True, UITheme.TEXT_DIM), (500, 22))
        start_x, start_y = 50, 100
        cell_w, cell_h = 100, 30
        if state.editor_df is not None:
            cols = state.editor_df.columns
            for c_idx, col_name in enumerate(cols):
                cx = start_x + (c_idx * cell_w)
                if cx > 1200: break
                pygame.draw.rect(self.screen, (40, 40, 50), (cx, start_y - 30, cell_w, 30))
                pygame.draw.rect(self.screen, (80, 80, 80), (cx, start_y - 30, cell_w, 30), 1)
                self.screen.blit(self.font_small.render(col_name[:12], True, (255, 255, 255)), (cx + 5, start_y - 25))
            row_limit = 15
            visible_df = state.editor_df.iloc[int(state.editor_scroll_y):int(state.editor_scroll_y)+row_limit]
            for r_idx, (idx, row) in enumerate(visible_df.iterrows()):
                actual_row_idx = int(state.editor_scroll_y) + r_idx
                ry = start_y + (r_idx * cell_h)
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
                    if is_selected: pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, rect, 2)
        for b in [layout.btn_editor_save, layout.btn_editor_exit]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_bold)

    def draw_ai_loading(self, mouse_pos):
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
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        if UITheme.BG_DARK[0] < 50: overlay.fill((0, 0, 0, 200))
        else: overlay.fill((255, 255, 255, 120))
        self.screen.blit(overlay, (0,0))
        w, h = 850, 560
        x, y = (1280 - w)//2, (720 - h)//2
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, rect)
        pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, rect, 2)
        UITheme.draw_bracket(self.screen, rect, UITheme.ACCENT_ORANGE)
        self.screen.blit(self.font_header.render("AI ANALYSIS REPORT", True, UITheme.TEXT_OFF_WHITE), (x + 20, y + 20))
        content_x = x + 40
        content_y = y + 95
        content_w = w - 80
        content_h = h - 190
        content_rect = pygame.Rect(content_x, content_y, content_w, content_h)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, content_rect, border_radius=6)
        pygame.draw.rect(self.screen, UITheme.GRID_COLOR, content_rect, 1, border_radius=6)
        pad = 14
        inner_rect = content_rect.inflate(-pad*2, -pad*2)
        text_x = inner_rect.x + 10
        wrap_w = inner_rect.w - 20
        self.screen.set_clip(inner_rect)
        if not hasattr(state, "ai_popup_scroll_y"): state.ai_popup_scroll_y = 0
        scroll_y = state.ai_popup_scroll_y
        y_cursor = inner_rect.y - scroll_y
        content_start_y = inner_rect.y
        data = state.ai_popup_data or {}
        summary = data.get("summary", "No Data.")
        self.screen.blit(self.font_bold.render("SUMMARY", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
        y_cursor += 34
        y_cursor += UITheme.render_terminal_text(self.screen, summary, (text_x , y_cursor), self.font_main, UITheme.TEXT_OFF_WHITE, wrap_w) + 12
        anomalies = data.get("anomalies", []) or []
        if anomalies:
            self.screen.blit(self.font_bold.render("DETECTED ANOMALIES", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
            y_cursor += 34
            for idx, item in enumerate(anomalies, start=1):
                line = f"{idx}. {item}"
                y_cursor += UITheme.render_terminal_text(self.screen, line, (text_x, y_cursor), self.font_main, (255, 120, 120), wrap_w) + 6
            y_cursor += 8
        next_steps = data.get("next_steps", "")
        if next_steps:
            self.screen.blit(self.font_bold.render("NEXT STEPS", True, UITheme.ACCENT_ORANGE), (inner_rect.x, y_cursor))
            y_cursor += 34
            y_cursor += UITheme.render_terminal_text(self.screen, next_steps, (text_x, y_cursor), self.font_main, UITheme.TEXT_OFF_WHITE, wrap_w) + 10
        content_end_y_no_scroll = y_cursor + scroll_y
        total_content_h = content_end_y_no_scroll - content_start_y
        max_scroll = max(0, int(total_content_h - inner_rect.h + 20))
        state.ai_popup_scroll_y = max(0, min(state.ai_popup_scroll_y, max_scroll))
        self.screen.set_clip(None)
        layout.btn_popup_close.check_hover(mouse_pos)
        layout.btn_popup_close.draw(self.screen, self.font_bold)
        layout.btn_popup_download.check_hover(mouse_pos)
        layout.btn_popup_download.draw(self.screen, self.font_bold)

    def draw_api_config_modal(self, mouse_pos):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0,0))
        w, h = 600, 400
        x, y = (1280 - w)//2, (720 - h)//2
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, rect)
        pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, rect, 2)
        UITheme.draw_bracket(self.screen, rect, UITheme.ACCENT_ORANGE)
        self.screen.blit(self.font_header.render("CONFIGURE AI CREDENTIALS", True, UITheme.TEXT_OFF_WHITE), (x + 20, y + 20))
        self.screen.blit(self.font_main.render("Enter Azure OpenAI details. Use CTRL+V to paste.", True, UITheme.TEXT_DIM), (x + 20, y + 60))
        lbl_key = self.font_bold.render("API KEY:", True, UITheme.ACCENT_ORANGE)
        self.screen.blit(lbl_key, (x + 40, y + 100))
        key_rect = pygame.Rect(x + 40, y + 130, 520, 40)
        col_key = (30, 30, 40) if state.api_active_field != 0 else (50, 50, 60)
        border_key = UITheme.ACCENT_ORANGE if state.api_active_field == 0 else UITheme.GRID_COLOR
        pygame.draw.rect(self.screen, col_key, key_rect)
        pygame.draw.rect(self.screen, border_key, key_rect, 1)
        key_txt = state.api_key_buffer + ("|" if state.api_active_field == 0 and (pygame.time.get_ticks()//500)%2==0 else "")
        display_key = key_txt if len(key_txt) < 4 else "*" * (len(key_txt)-1) + key_txt[-1]
        self.screen.blit(self.font_main.render(display_key, True, UITheme.TEXT_OFF_WHITE), (key_rect.x + 10, key_rect.y + 10))
        lbl_end = self.font_bold.render("ENDPOINT URL:", True, UITheme.ACCENT_ORANGE)
        self.screen.blit(lbl_end, (x + 40, y + 190))
        end_rect = pygame.Rect(x + 40, y + 220, 520, 40)
        col_end = (30, 30, 40) if state.api_active_field != 1 else (50, 50, 60)
        border_end = UITheme.ACCENT_ORANGE if state.api_active_field == 1 else UITheme.GRID_COLOR
        pygame.draw.rect(self.screen, col_end, end_rect)
        pygame.draw.rect(self.screen, border_end, end_rect, 1)
        end_txt = state.api_endpoint_buffer + ("|" if state.api_active_field == 1 and (pygame.time.get_ticks()//500)%2==0 else "")
        self.screen.blit(self.font_main.render(end_txt[-50:], True, UITheme.TEXT_OFF_WHITE), (end_rect.x + 10, end_rect.y + 10))
        self.screen.blit(self.font_small.render("Press TAB to switch fields. Press ENTER to Save.", True, UITheme.TEXT_DIM), (x + 40, y + 280))

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

    def draw_metadata_editor(self, mouse_pos):
        panel_rect = pygame.Rect(840, 80, 420, 550)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, panel_rect)
        UITheme.draw_bracket(self.screen, panel_rect, UITheme.ACCENT_ORANGE)
        self.screen.blit(self.font_bold.render("EDITING NOTES (CTRL+C/V to Copy/Paste):", True, UITheme.TEXT_DIM), (860, 95))
        
        text_area_rect = pygame.Rect(850, 125, 400, 465)
        pygame.draw.rect(self.screen, UITheme.BG_DARK, text_area_rect)
        pygame.draw.rect(self.screen, UITheme.GRID_COLOR, text_area_rect, 1)
        
        self.screen.set_clip(text_area_rect)
        cursor_char = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        display_text = state.meta_input_notes[:state.notes_cursor_idx] + cursor_char + state.meta_input_notes[state.notes_cursor_idx:]
        start_pos = (855, 130 - state.notes_scroll_y)
        total_h = UITheme.render_terminal_text(self.screen, display_text, start_pos, self.font_main, UITheme.TEXT_OFF_WHITE, 390)
        self.screen.set_clip(None)
        
        if total_h > 465:
            scroll_pct = state.notes_scroll_y / total_h
            bar_h = (465 / total_h) * 465
            bar_y = 125 + (scroll_pct * 465)
            pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, (1245, bar_y, 4, bar_h))
        
        layout.btn_save_meta.check_hover(mouse_pos)
        layout.btn_save_meta.draw(self.screen, self.font_bold)

    def draw_delete_confirm_modal(self, mouse_pos):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 230))
        self.screen.blit(overlay, (0,0))
        
        w, h = 500, 250
        x, y = (1280 - w)//2, (720 - h)//2
        rect = pygame.Rect(x, y, w, h)
        
        pygame.draw.rect(self.screen, (40, 10, 10), rect)
        pygame.draw.rect(self.screen, (255, 0, 0), rect, 2)
        
        self.screen.blit(self.font_header.render("DANGER ZONE", True, (255, 50, 50)), (x + 140, y + 30))
        self.screen.blit(self.font_bold.render("PERMANENTLY DELETE PROJECT?", True, UITheme.TEXT_OFF_WHITE), (x + 110, y + 90))
        self.screen.blit(self.font_main.render("This action cannot be undone.", True, UITheme.TEXT_DIM), (x + 140, y + 120))
        
        layout.btn_del_confirm.check_hover(mouse_pos)
        layout.btn_del_confirm.draw(self.screen, self.font_bold)
        
        layout.btn_del_cancel.check_hover(mouse_pos)
        layout.btn_del_cancel.draw(self.screen, self.font_bold)

    def draw_dashboard(self, mouse_pos, tree_ui, ai_engine, settings_menu):
        self.screen.fill(UITheme.BG_DARK)
        UITheme.draw_grid(self.screen)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, (0, 0, 1280, 70))
        pygame.draw.line(self.screen, UITheme.ACCENT_ORANGE, (0, 70), (1280, 70), 2)
        proj_name = os.path.basename(state.selected_project_path).upper() if state.selected_project_path else "NO PROJECT"
        header_txt = f"SCI-GIT // {proj_name} // {state.researcher_name.upper()}"
        self.screen.blit(self.font_bold.render(header_txt, True, UITheme.ACCENT_ORANGE), (20, 10))
        
        for b in [layout.btn_menu_file, layout.btn_menu_edit, layout.btn_menu_ai]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_small)
        layout.btn_home.check_hover(mouse_pos)
        layout.btn_home.draw(self.screen, self.font_small)

        def draw_dropdown_bg(rect):
            pygame.draw.rect(self.screen, UITheme.BG_DARK, rect)
            pygame.draw.rect(self.screen, UITheme.GRID_COLOR, rect, 1)

        if state.show_file_dropdown:
            draw_dropdown_bg(pygame.Rect(20, 66, 140, 134)) 
            for b in [layout.dd_file_export, layout.dd_file_move, layout.dd_file_rename, layout.dd_file_delete, layout.dd_file_print_map]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_small)

        if state.show_edit_dropdown:
            draw_dropdown_bg(pygame.Rect(90, 66, 110, 78))
            for b in [layout.dd_edit_undo, layout.dd_edit_redo, layout.dd_edit_file]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_small)

        if state.show_ai_dropdown:
            # Increased height for the new button
            draw_dropdown_bg(pygame.Rect(160, 66, 180, 130))
            for b in [layout.dd_ai_analyze, layout.dd_ai_summary, layout.dd_ai_node_simplified, layout.dd_ai_project_simplified, layout.dd_ai_inconsistency]:
                b.check_hover(mouse_pos)
                b.draw(self.screen, self.font_small)

        search_rect = pygame.Rect(850, 45, 200, 20)
        is_light = UITheme.BG_DARK[0] > 150
        input_bg = UITheme.PANEL_GREY if is_light else UITheme.BG_DARK
        pygame.draw.rect(self.screen, input_bg, search_rect)
        border_col = UITheme.ACCENT_ORANGE if state.search_active else UITheme.TEXT_DIM
        pygame.draw.rect(self.screen, border_col, search_rect, 1)
        self.screen.blit(self.font_small.render("SEARCH:", True, UITheme.TEXT_DIM), (800, 48))
        display_text = state.search_text
        if state.search_active and (pygame.time.get_ticks() % 1000) > 500: display_text += "_"
        text_surf = self.font_small.render(display_text, True, UITheme.TEXT_OFF_WHITE)
        if text_surf.get_width() > 190:
            display_text = "..." + state.search_text[-20:]
            if state.search_active and (pygame.time.get_ticks() % 1000) > 500: display_text += "_"
            text_surf = self.font_small.render(display_text, True, UITheme.TEXT_OFF_WHITE)
        self.screen.blit(text_surf, (855, 48))

        ai_status = "AI ONLINE" if ai_engine.client else "AI OFFLINE"
        ai_col = (0, 255, 150) if ai_engine.client else (200, 50, 50)
        self.screen.blit(self.font_main.render(ai_status, True, ai_col), (1150, 10))
        self.screen.blit(self.font_main.render(f"> {state.status_msg}", True, UITheme.TEXT_DIM), (850, 15))

        tree_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        if pygame.mouse.get_pressed()[0] and not state.show_ai_popup and not state.show_api_popup and not state.show_delete_confirm:
            if not state.pan_mode:
                tree_ui.update_drag(mouse_pos, (20, 80, 800, 600))
        else:
            tree_ui.dragged_node_id = None
            
        tree_ui.draw(tree_surf, mouse_pos)
        tree_ui.draw_minimap(tree_surf, tree_surf.get_rect(), self.icons)
        self.screen.blit(tree_surf, (20, 80))
        UITheme.draw_bracket(self.screen, (20, 80, 800, 600), UITheme.ACCENT_ORANGE)
        
        # Draw Canvas Controls (Bottom Left)
        for b in [layout.btn_zoom_in, layout.btn_zoom_out, layout.btn_pan_mode]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_bold)
            
        if state.pan_mode:
            pygame.draw.rect(self.screen, UITheme.ACCENT_ORANGE, layout.btn_pan_mode.rect, 2)

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
                    
                    if node["id"] in state.inconsistent_nodes:
                        layout.btn_inconsistency_alert.rect.topleft = (mx, my + 80)
                        layout.btn_inconsistency_alert.check_hover(mouse_pos)
                        layout.btn_inconsistency_alert.draw(self.screen, self.font_bold)

        side_rect = (840, 80, 420, 600)
        pygame.draw.rect(self.screen, UITheme.PANEL_GREY, side_rect)
        UITheme.draw_bracket(self.screen, side_rect, (100, 100, 100))

        if not state.is_editing_metadata:
            if state.current_plot: 
                self.screen.blit(state.current_plot, (850, 100))
                plot_rect = pygame.Rect(850, 100, 400, 300)
                pygame.draw.rect(self.screen, (50, 50, 55), plot_rect, 1)
                
                layout.btn_axis_gear.check_hover(mouse_pos)
                r = layout.btn_axis_gear.rect
                if self.icons.get('graph'):
                    self.screen.blit(self.icons['graph'], (r.x, r.y))
                else:
                    layout.btn_axis_gear.draw(self.screen, self.font_bold)
                
                if layout.btn_axis_gear.is_hovered: pygame.draw.rect(self.screen, (255, 255, 255), r, 1)

                if plot_rect.collidepoint(mouse_pos) and state.plot_context and not state.show_ai_popup and not state.show_api_popup:
                    self.draw_plot_tooltip(mouse_pos)
            if state.current_analysis:
                analysis_area = pygame.Rect(850, 410, 390, 200)
                self.screen.set_clip(analysis_area)
                y_pos = 410 - state.analysis_scroll_y
                summary_text = state.current_analysis.get('summary', "")
                h = UITheme.render_terminal_text(self.screen, summary_text, (855, y_pos), self.font_main, UITheme.TEXT_OFF_WHITE, 380)
                if len(state.selected_ids) == 1:
                    meta_txt = f"\nRESEARCH NOTES:\n{state.meta_input_notes}"
                    UITheme.render_terminal_text(self.screen, meta_txt, (855, y_pos + h), self.font_main, UITheme.ACCENT_ORANGE, 380)
                self.screen.set_clip(None)
        else:
            self.draw_metadata_editor(mouse_pos)

        if state.active_branch == "main": layout.btn_branch.text = "NEW BRANCH"
        else: layout.btn_branch.text = "RETURN TO MAIN"

        for b in [layout.btn_new_node, layout.btn_branch]:
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_main)
        
        if state.is_processing:
            if state.processing_mode == "AI": self.draw_ai_loading(mouse_pos)
            else: draw_loading_overlay(self.screen, self.font_bold)
        
        if state.show_conversion_dialog: self.draw_conversion_dialog(mouse_pos)
        if state.show_ai_popup: self.draw_ai_popup(mouse_pos)
        if state.show_delete_confirm: self.draw_delete_confirm_modal(mouse_pos)
        
        if state.show_api_popup: self.draw_api_config_modal(mouse_pos)
        
        if state.show_settings:
            settings_menu.draw(self.screen)
            if self.icons.get('settings'):
                r = layout.btn_main_settings.rect
                self.screen.blit(self.icons['settings'], (r.x, r.y))
            else: layout.btn_main_settings.draw(self.screen, self.font_bold)
        else:
            if self.icons.get('settings'):
                r = layout.btn_main_settings.rect
                layout.btn_main_settings.check_hover(mouse_pos)
                self.screen.blit(self.icons['settings'], (r.x, r.y))
                if layout.btn_main_settings.is_hovered: pygame.draw.rect(self.screen, (255, 255, 255), r, 1)
            else:
                layout.btn_main_settings.check_hover(mouse_pos)
                layout.btn_main_settings.draw(self.screen, self.font_bold)