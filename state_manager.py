# --- FILE: state_manager.py ---
class AppState:
    def __init__(self):
        # Core identifiers
        self.selected_ids =[] 
        self.head_id = None
        self.active_branch = "main"
        
        # Plotting / Analysis
        self.current_plot = None
        self.current_analysis = None
        self.plot_context = None
        
        # Axis Selector
        self.show_axis_selector = False
        
        # Processing / Status
        self.is_processing = False
        self.processing_mode = "NORMAL"
        self.needs_tree_update = False 
        self.status_msg = "SYSTEM READY"
        
        # Conversion Dialog
        self.show_conversion_dialog = False
        self.pending_conversion = None 
        
        # AI Result Popup
        self.show_ai_popup = False
        self.ai_popup_data = None
        
        # API CONFIGURATION POPUP
        self.show_api_popup = False
        self.api_key_buffer = ""
        self.api_endpoint_buffer = ""
        self.api_active_field = 0 # 0 = Key, 1 = Endpoint
        
        # Extended UI Toggles
        self.show_ai_panel = False          
        self.is_editing_metadata = False
        self.show_delete_confirm = False 
        
        # Dropdowns
        self.show_file_dropdown = False
        self.show_edit_dropdown = False
        self.show_ai_dropdown = False
        self.show_settings = False 
        
        # ADD POPUP & LINKAGE
        self.show_add_popup = False
        self.linkage_source = None
        
        # Editor State
        self.editor_df = None
        self.editor_file_path = None
        self.editor_scroll_y = 0
        self.editor_selected_cell = None 
        self.editor_input_buffer = ""

        # Global Input
        self.search_text = ""
        self.search_active = False
        
        # Metadata / Notes
        self.meta_input_notes = ""
        self.notes_scroll_y = 0
        self.notes_cursor_idx = 0
        
        # Inconsistency State
        self.inconsistent_nodes =[]
        self.inconsistency_data = None
        
        # App Flow
        self.researcher_name = ""
        self.show_login_box = False
        self.selected_project_path = ""

        self.analysis_scroll_y = 0
        self.stop_ai_requested = False
        self.minimap_collapsed = False
        
        # Undo/Redo
        self.redo_stack = {} 
        
        # Canvas Controls
        self.pan_mode = False 

state = AppState()