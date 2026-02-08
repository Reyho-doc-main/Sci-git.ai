# --- FILE: state_manager.py ---
class AppState:
    def __init__(self):
        # Core identifiers
        self.selected_ids = [] 
        self.head_id = None
        self.active_branch = "main"
        
        # Plotting / Analysis
        self.current_plot = None
        self.current_analysis = None
        self.plot_context = None  # {df, x_col, y_col, type}
        
        # Axis Selector
        self.show_axis_selector = False
        
        # Processing / Status
        self.is_processing = False
        self.needs_tree_update = False 
        self.status_msg = "SYSTEM READY"
        
        # Conversion Dialog
        self.show_conversion_dialog = False
        self.pending_conversion = None 
        
        # Extended UI Toggles
        self.show_ai_panel = False          
        self.is_editing_metadata = False
        
        # GLOBAL EDITOR STATE (Moved from main.py)
        self.editor_df = None
        self.editor_file_path = None
        self.editor_scroll_y = 0
        self.editor_selected_cell = None 
        self.editor_input_buffer = ""

        # GLOBAL INPUT STATE
        self.search_text = ""
        self.search_active = False
        self.meta_input_notes = ""
        self.meta_input_temp = ""
        self.meta_input_sid = ""
        self.active_field = "notes"
        
        # APP FLOW
        self.researcher_name = ""
        self.show_login_box = False
        self.selected_project_path = ""

state = AppState()