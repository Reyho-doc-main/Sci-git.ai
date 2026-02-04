class AppState:
    def __init__(self):
        self.selected_id = None
        self.head_id = None
        self.active_branch = "main"
        
        self.current_plot = None
        self.current_analysis = None
        
        self.is_processing = False
        self.needs_tree_update = False # NEW: Flag to refresh UI safely
        self.status_msg = "SYSTEM READY"

state = AppState()