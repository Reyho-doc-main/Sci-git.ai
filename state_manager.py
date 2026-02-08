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
        self.axis_selector_mode = "primary"  # 'primary' or 'secondary'
        
        # Processing / Status
        self.is_processing = False
        self.needs_tree_update = False 
        self.status_msg = "SYSTEM READY"
        
        # Conversion Dialog
        self.show_conversion_dialog = False
        self.pending_conversion = None 
        
        # Extended UI Toggles (from StateManager)
        self.show_ai_panel = False          # For slide-out chat
        self.is_editing_metadata = False    # Metadata editing mode
        
        # Threading / Worker (from StateManager)
        self.worker_result_queue = []       # Simple list to check for results

state = AppState()