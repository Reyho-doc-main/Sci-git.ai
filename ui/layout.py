# --- FILE: ui/layout.py ---
from ui.components import Button
from settings import UITheme

SCREEN_CENTER_X = 1280 // 2
BTN_WIDTH = 280
BTN_X = SCREEN_CENTER_X - (BTN_WIDTH // 2)

class UILayout:
    def __init__(self):
        # SPLASH
        self.btn_new = Button(BTN_X, 420, BTN_WIDTH, 45, "CREATE NEW PROJECT", UITheme.ACCENT_ORANGE)
        self.btn_load = Button(BTN_X, 480, BTN_WIDTH, 45, "CONTINUE PROJECT", UITheme.ACCENT_ORANGE)
        self.btn_import = Button(BTN_X, 540, BTN_WIDTH, 45, "UPLOAD PROJECT", UITheme.ACCENT_ORANGE)
        self.btn_confirm = Button(BTN_X, 520, BTN_WIDTH, 45, "ENTER LABORATORY", (0, 180, 100))
        
        # DASHBOARD - BOTTOM BAR
        self.btn_new_node = Button(850, 640, 180, 40, "NEW NODE", UITheme.ACCENT_ORANGE)
        self.btn_branch = Button(1050, 640, 180, 40, "NEW BRANCH", UITheme.NODE_BRANCH)
        
        # DASHBOARD - CONTEXT ICONS
        self.btn_add_manual = Button(0, 0, 32, 32, "+", UITheme.ACCENT_ORANGE) 
        self.btn_edit_meta = Button(0, 0, 32, 32, "D", UITheme.NODE_MAIN)
        self.btn_save_meta = Button(855, 600, 390, 30, "SAVE TO SNAPSHOT", (0, 150, 255))
        
        self.btn_conv_yes = Button(500, 400, 100, 40, "YES", (0, 180, 100))
        self.btn_conv_no = Button(680, 400, 100, 40, "NO", (200, 50, 50))
        
        # DASHBOARD - TOP RIGHT
        self.btn_axis_gear = Button(1210, 100, 30, 30, "", (80, 80, 90)) 
        self.btn_main_settings = Button(1230, 10, 30, 30, "*", (80, 80, 90))

        # HOME
        self.btn_home = Button(1140, 42, 90, 26, "HOME", UITheme.PANEL_GREY)
        self.btn_home.fill_color = "BG_DARK"
        
        # ONBOARDING
        self.btn_skip_onboarding = Button(1150, 20, 100, 35, "SKIP >>", UITheme.TEXT_DIM)
        self.btn_onboard_upload = Button(SCREEN_CENTER_X - 150, 450, 300, 50, "UPLOAD FIRST EXPERIMENT", UITheme.ACCENT_ORANGE)

        # --- TOP MENU BAR ---
        self.btn_menu_file = Button(20, 45, 60, 20, "FILE", UITheme.PANEL_GREY)
        self.btn_menu_edit = Button(90, 45, 60, 20, "EDIT", UITheme.PANEL_GREY)
        self.btn_menu_ai = Button(160, 45, 40, 20, "AI", UITheme.PANEL_GREY)
        
        # --- DROPDOWN ITEMS ---
        # File Dropdown (Expanded)
        self.dd_file_export = Button(20, 68, 140, 24, "EXPORT PROJECT", UITheme.PANEL_GREY)
        self.dd_file_move = Button(20, 94, 140, 24, "MOVE PROJECT", UITheme.PANEL_GREY)
        self.dd_file_rename = Button(20, 120, 140, 24, "RENAME PROJECT", UITheme.PANEL_GREY) # NEW
        self.dd_file_delete = Button(20, 146, 140, 24, "DELETE PROJECT", UITheme.PANEL_GREY)
        self.dd_file_print_map = Button(20, 172, 140, 24, "PRINT MAPPING", UITheme.PANEL_GREY)
        
        # Edit Dropdown
        self.dd_edit_undo = Button(90, 68, 110, 24, "UNDO", UITheme.PANEL_GREY)
        self.dd_edit_redo = Button(90, 94, 110, 24, "REDO", UITheme.PANEL_GREY)
        self.dd_edit_file = Button(90, 120, 110, 24, "EDIT FILE", UITheme.PANEL_GREY)
        
        # AI Dropdown
        self.dd_ai_analyze = Button(160, 68, 160, 24, "ANALYZE PROJECT", UITheme.PANEL_GREY)
        self.dd_ai_summary = Button(160, 94, 160, 24, "AI NODE SUMMARY", UITheme.PANEL_GREY)
        self.dd_ai_simplified = Button(160, 120, 160, 24, "SIMPLIFIED REPORT", UITheme.PANEL_GREY) # NEW
        self.dd_ai_inconsistency = Button(160, 146, 160, 24, "FIND INCONSISTENCIES", UITheme.PANEL_GREY)

        for b in [
            self.btn_menu_file, self.btn_menu_edit, self.btn_menu_ai,
            self.dd_file_export, self.dd_file_move, self.dd_file_rename, self.dd_file_delete, self.dd_file_print_map,
            self.dd_edit_undo, self.dd_edit_redo, self.dd_edit_file,
            self.dd_ai_analyze, self.dd_ai_summary, self.dd_ai_simplified, self.dd_ai_inconsistency
        ]:
            b.fill_color = "BG_DARK"

        # EDITOR
        self.btn_editor_save = Button(1050, 650, 200, 40, "SAVE CHANGES", (0, 180, 100))
        self.btn_editor_exit = Button(20, 650, 150, 40, "CANCEL", (200, 50, 50))

        # AI LOADING
        self.btn_ai_stop = Button(SCREEN_CENTER_X - 100, 500, 200, 50, "ABORT SEQUENCE", (200, 50, 50))

        # AI POPUP RESULT
        self.btn_popup_close = Button(SCREEN_CENTER_X - 210, 550, 200, 40, "CLOSE", (200, 50, 50))
        self.btn_popup_download = Button(SCREEN_CENTER_X + 10, 550, 200, 40, "DOWNLOAD PDF", UITheme.ACCENT_ORANGE)

        # --- CANVAS CONTROLS ---
        # Changed "H" to "P" for Pan Mode
        self.btn_zoom_in = Button(30, 630, 30, 30, "+", UITheme.PANEL_GREY)
        self.btn_zoom_out = Button(70, 630, 30, 30, "-", UITheme.PANEL_GREY)
        self.btn_pan_mode = Button(110, 630, 30, 30, "P", UITheme.PANEL_GREY) 
        
        # --- INCONSISTENCY ALERT ---
        self.btn_inconsistency_alert = Button(0, 0, 32, 32, "!", (255, 50, 50))

        # --- DELETE CONFIRMATION MODAL ---
        self.btn_del_confirm = Button(SCREEN_CENTER_X - 110, 400, 100, 40, "CONFIRM", (200, 50, 50))
        self.btn_del_cancel = Button(SCREEN_CENTER_X + 10, 400, 100, 40, "CANCEL", UITheme.PANEL_GREY)

layout = UILayout()