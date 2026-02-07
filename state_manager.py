class AppState:
    def __init__(self):
        self.selected_ids = [] 
        self.head_id = None
        self.active_branch = "main"
        
        self.current_plot = None
        self.current_analysis = None
        
        self.plot_context = None # {df, x_col, y_col, type}
        self.show_axis_selector = False
        self.axis_selector_mode = "primary" # 'primary' or 'secondary' if we add that later
        
        self.is_processing = False
        self.needs_tree_update = False 
        self.status_msg = "SYSTEM READY"

        # Conversion Dialog
        self.show_conversion_dialog = False
        self.pending_conversion = None 

state = AppState()