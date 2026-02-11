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
        self.btn_export = Button(850, 640, 180, 40, "GENERATE REPORT", UITheme.ACCENT_ORANGE)
        self.btn_branch = Button(1050, 640, 180, 40, "NEW BRANCH", UITheme.NODE_BRANCH)
        
        # DASHBOARD - CONTEXT ICONS
        self.btn_add_manual = Button(0, 0, 32, 32, "+", UITheme.ACCENT_ORANGE) 
        self.btn_edit_meta = Button(0, 0, 32, 32, "i", UITheme.NODE_MAIN)
        self.btn_save_meta = Button(855, 500, 390, 40, "SAVE TO SNAPSHOT", (0, 150, 255))
        self.btn_conv_yes = Button(500, 400, 100, 40, "YES", (0, 180, 100))
        self.btn_conv_no = Button(680, 400, 100, 40, "NO", (200, 50, 50))
        
        # DASHBOARD - TOP RIGHT
        self.btn_axis_gear = Button(1210, 100, 30, 30, "O", (80, 80, 90)) 
        self.btn_main_settings = Button(1230, 10, 30, 30, "*", (80, 80, 90))

        # ONBOARDING
        self.btn_skip_onboarding = Button(1150, 20, 100, 35, "SKIP >>", UITheme.TEXT_DIM)
        self.btn_onboard_upload = Button(SCREEN_CENTER_X - 150, 450, 300, 50, "UPLOAD FIRST EXPERIMENT", UITheme.ACCENT_ORANGE)

        # --- TOP MENU BAR ---
        self.btn_menu_file = Button(20, 45, 60, 20, "FILE", UITheme.PANEL_GREY)
        self.btn_menu_edit = Button(90, 45, 60, 20, "EDIT", UITheme.PANEL_GREY)
        self.btn_menu_ai = Button(160, 45, 40, 20, "AI", UITheme.PANEL_GREY)
        
        # --- DROPDOWN ITEMS ---
        # File Dropdown
        self.dd_file_export = Button(20, 68, 140, 24, "EXPORT PROJECT", UITheme.PANEL_GREY)
        
        # Edit Dropdown
        self.dd_edit_undo = Button(90, 68, 110, 24, "UNDO", UITheme.PANEL_GREY)
        self.dd_edit_redo = Button(90, 94, 110, 24, "REDO", UITheme.PANEL_GREY)
        self.dd_edit_file = Button(90, 120, 110, 24, "EDIT FILE", UITheme.PANEL_GREY)
        
        # AI Dropdown
        self.dd_ai_analyze = Button(160, 68, 140, 24, "ANALYZE PROJECT", UITheme.PANEL_GREY)

        # EDITOR
        self.btn_editor_save = Button(1050, 650, 200, 40, "SAVE CHANGES", (0, 180, 100))
        self.btn_editor_exit = Button(20, 650, 150, 40, "CANCEL", (200, 50, 50))

        # AI LOADING
        self.btn_ai_stop = Button(SCREEN_CENTER_X - 100, 500, 200, 50, "ABORT SEQUENCE", (200, 50, 50))

        # AI POPUP RESULT
        self.btn_popup_close = Button(SCREEN_CENTER_X - 210, 550, 200, 40, "CLOSE", (200, 50, 50))
        self.btn_popup_download = Button(SCREEN_CENTER_X + 10, 550, 200, 40, "DOWNLOAD PDF", UITheme.ACCENT_ORANGE)

layout = UILayout()