import pygame
import os
import sys
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, simpledialog
from queue import Queue

# --- MODULES ---
from state_manager import state
from database.db_handler import DBHandler
from ui.elements import VersionTree
from ui.layout import layout  # Import the buttons
from ui.screens import RenderEngine # Import the drawing logic
from core.watcher import start_watcher
from engine.ai import ScienceAI
from core.processor import export_to_report
from core.workers import TaskQueue, WorkerController
from core.hashing import save_to_vault, get_file_hash

# --- INIT ---
pygame.init()
root = tk.Tk()
root.withdraw() 
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("SCI-GIT // Research Version Control")

# --- ICON SETUP ---
try:
    if os.path.exists("logo.jpg"):
        icon_surf = pygame.image.load("logo.jpg")
        pygame.display.set_icon(icon_surf)
except Exception as e:
    print(f"Icon load failed: {e}")

clock = pygame.time.Clock()

# --- OBJECTS ---
db = None 
ai_engine = ScienceAI()
tree_ui = VersionTree()
event_queue = Queue()
task_manager = TaskQueue()
render_engine = RenderEngine(screen)
worker_ctrl = None # Will be init after DB load

# --- STATE CONSTANTS ---
STATE_SPLASH = "SPLASH"
STATE_DASHBOARD = "DASHBOARD"
STATE_ONBOARDING = "ONBOARDING"
STATE_EDITOR = "EDITOR"
current_state = STATE_SPLASH

def init_project(path):
    for folder in ["data", "exports", "logs", ".sci_vault"]: os.makedirs(os.path.join(path, folder), exist_ok=True)

def load_database_safe(path):
    global db, worker_ctrl
    if db: 
        try: db.close()
        except: pass
    db = DBHandler(path)
    worker_ctrl = WorkerController(db, ai_engine) # Connect worker to DB

def save_editor_changes():
    if not state.selected_ids: return
    
    # Commit pending buffer before saving
    if state.editor_selected_cell:
        r, c = state.editor_selected_cell
        try:
            val = float(state.editor_input_buffer)
            state.editor_df.iloc[r, c] = val
        except ValueError:
            state.editor_df.iloc[r, c] = state.editor_input_buffer
        state.editor_selected_cell = None

    state.status_msg = "SAVING & VERSIONING..."
    
    task_manager.add_task(worker_ctrl.worker_save_editor_changes, [
        state.selected_ids[0], 
        state.editor_file_path, 
        state.editor_df.copy(), 
        state.selected_project_path
    ])

def perform_undo():
    if not state.selected_ids: return
    node_id = state.selected_ids[0]
    raw = db.get_experiment_by_id(node_id)
    if not raw: return
    state.status_msg = "UNDOING..."
    task_manager.add_task(worker_ctrl.worker_undo, [node_id, raw[3], state.selected_project_path, state.redo_stack.get(node_id, [])])

def perform_redo():
    if not state.selected_ids: return
    node_id = state.selected_ids[0]
    if node_id not in state.redo_stack or not state.redo_stack[node_id]:
        state.status_msg = "NOTHING TO REDO"
        return
    raw = db.get_experiment_by_id(node_id)
    if not raw: return
    redo_hash = state.redo_stack[node_id].pop()
    state.status_msg = "REDOING..."
    task_manager.add_task(worker_ctrl.worker_redo, [node_id, raw[3], state.selected_project_path, redo_hash])

# ==============================================================================
# GAME LOOP
# ==============================================================================
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()
    
    task_manager.process_results()
    
    if not state.is_processing:
        if "VERSION SAVED" in state.status_msg or "RESTORED" in state.status_msg:
             if state.selected_ids:
                 task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids])
                 if "VERSION SAVED" in state.status_msg: state.status_msg = "SAVED."
                 elif "RESTORED" in state.status_msg: state.status_msg = "READY."
    
    if not event_queue.empty() and not state.is_processing and worker_ctrl:
        ev = event_queue.get()
        if ev["type"] == "NEW_FILE":
            task_manager.add_task(worker_ctrl.worker_process_new_file, [ev["path"], state.head_id, state.active_branch, state.researcher_name])

    axis_selector_rect = pygame.Rect(850, 130, 200, 300)

    for event in events:
        if event.type == pygame.QUIT: running = False
        
        # --- EDITOR KEYBOARD INPUT ---
        if current_state == STATE_EDITOR and event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                # 1. Commit current buffer if valid
                if state.editor_selected_cell:
                    r, c = state.editor_selected_cell
                    try: state.editor_df.iloc[r, c] = float(state.editor_input_buffer)
                    except: state.editor_df.iloc[r, c] = state.editor_input_buffer
                
                # 2. Determine new pos
                if not state.editor_selected_cell:
                    new_r, new_c = 0, 0
                else:
                    r, c = state.editor_selected_cell
                    new_r, new_c = r, c
                    if event.key == pygame.K_UP: new_r = max(0, r - 1)
                    elif event.key == pygame.K_DOWN: new_r = min(len(state.editor_df)-1, r + 1)
                    elif event.key == pygame.K_LEFT: new_c = max(0, c - 1)
                    elif event.key == pygame.K_RIGHT: new_c = min(len(state.editor_df.columns)-1, c + 1)
                
                # 3. Apply & Scroll
                state.editor_selected_cell = (new_r, new_c)
                state.editor_input_buffer = str(state.editor_df.iloc[new_r, new_c])
                
                # Auto-Scroll Logic (15 is visible row count)
                if new_r < state.editor_scroll_y: state.editor_scroll_y = new_r
                if new_r >= state.editor_scroll_y + 15: state.editor_scroll_y = new_r - 14

            elif state.editor_selected_cell:
                if event.key == pygame.K_RETURN:
                    r, c = state.editor_selected_cell
                    try:
                        val = float(state.editor_input_buffer)
                        state.editor_df.iloc[r, c] = val
                    except ValueError:
                        state.editor_df.iloc[r, c] = state.editor_input_buffer
                    state.editor_selected_cell = None
                elif event.key == pygame.K_BACKSPACE:
                    state.editor_input_buffer = state.editor_input_buffer[:-1]
                else:
                    state.editor_input_buffer += event.unicode

        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LCTRL] and event.key == pygame.K_z and current_state == STATE_DASHBOARD:
                perform_undo()
            elif keys[pygame.K_RCTRL] and event.key == pygame.K_z and current_state == STATE_DASHBOARD:
                perform_undo()
            elif keys[pygame.K_LCTRL] and event.key == pygame.K_y and current_state == STATE_DASHBOARD:
                perform_redo()
            elif keys[pygame.K_RCTRL] and event.key == pygame.K_y and current_state == STATE_DASHBOARD:
                perform_redo()

        # --- MOUSE INPUT ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if current_state == STATE_EDITOR:
                if layout.btn_editor_save.check_hover(mouse_pos):
                    save_editor_changes()
                    current_state = STATE_DASHBOARD
                elif layout.btn_editor_exit.check_hover(mouse_pos):
                    current_state = STATE_DASHBOARD
                
                # GRID CLICK LOGIC
                if 50 < mouse_pos[0] < 1230 and 100 < mouse_pos[1] < 600:
                    rel_y = mouse_pos[1] - 100
                    row_idx = (rel_y // 30) + int(state.editor_scroll_y)
                    col_idx = (mouse_pos[0] - 50) // 100
                    
                    if 0 <= row_idx < len(state.editor_df) and 0 <= col_idx < len(state.editor_df.columns):
                        state.editor_selected_cell = (row_idx, col_idx)
                        state.editor_input_buffer = str(state.editor_df.iloc[row_idx, col_idx])
                    else:
                        state.editor_selected_cell = None

            elif current_state == STATE_DASHBOARD:
                if state.show_axis_selector:
                    if not axis_selector_rect.collidepoint(mouse_pos) and not layout.btn_axis_gear.check_hover(mouse_pos):
                        state.show_axis_selector = False
                    elif axis_selector_rect.collidepoint(mouse_pos) and state.plot_context:
                        df_ref = state.plot_context['df']
                        numeric_cols = df_ref.select_dtypes(include=['number']).columns
                        local_y = mouse_pos[1] - 160
                        idx = local_y // 25
                        if 0 <= idx < len(numeric_cols):
                            col_name = numeric_cols[idx]
                            if 850 <= mouse_pos[0] < 950: 
                                task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids, col_name, state.plot_context.get('y_col'), True])
                            else:
                                task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids, state.plot_context.get('x_col'), col_name, True])

                elif state.show_conversion_dialog:
                    if layout.btn_conv_yes.check_hover(mouse_pos):
                        file_path, col, unit = state.pending_conversion
                        task_manager.add_task(worker_ctrl.worker_perform_conversion, [file_path, col, unit, state.selected_ids])
                        state.show_conversion_dialog = False
                    elif layout.btn_conv_no.check_hover(mouse_pos):
                        state.show_conversion_dialog = False

                else:
                    # BUTTON CLICKS (Referring to layout object)
                    if layout.btn_menu_analyze.check_hover(mouse_pos):
                        task_manager.add_task(worker_ctrl.worker_analyze_branch, [state.active_branch])
                    
                    if layout.btn_menu_edit.check_hover(mouse_pos):
                        if len(state.selected_ids) == 1:
                            raw = db.get_experiment_by_id(state.selected_ids[0])
                            state.editor_file_path = raw[3]
                            state.editor_df = pd.read_csv(state.editor_file_path)
                            current_state = STATE_EDITOR
                            state.editor_selected_cell = None
                            state.status_msg = "EDITING MODE ACTIVE"

                    if layout.btn_menu_file.check_hover(mouse_pos):
                        task_manager.add_task(worker_ctrl.worker_export_project, [state.selected_project_path])
                    
                    if layout.btn_undo.check_hover(mouse_pos):
                        perform_undo()
                    
                    if layout.btn_redo.check_hover(mouse_pos):
                        perform_redo()

                    if layout.btn_axis_gear.check_hover(mouse_pos): 
                        state.show_axis_selector = not state.show_axis_selector
                    
                    if len(state.selected_ids) == 1 and layout.btn_add_manual.check_hover(mouse_pos):
                        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
                        if path: task_manager.add_task(worker_ctrl.worker_process_new_file, [path, state.selected_ids[0], state.active_branch, state.researcher_name])
                    
                    elif len(state.selected_ids) == 1 and layout.btn_edit_meta.check_hover(mouse_pos): 
                        state.is_editing_metadata = not state.is_editing_metadata
                    
                    elif state.is_editing_metadata and layout.btn_save_meta.check_hover(mouse_pos):
                        db.update_metadata(state.selected_ids[0], state.meta_input_notes)
                        state.is_editing_metadata = False
                        task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids])
                    
                    elif layout.btn_snapshot_export.check_hover(mouse_pos):
                        task_manager.add_task(worker_ctrl.worker_export_project, [state.selected_project_path])
                    elif layout.btn_branch.check_hover(mouse_pos):
                        new_branch = simpledialog.askstring("New Branch", "Name:")
                        if new_branch:
                            state.active_branch = new_branch
                            state.status_msg = f"BRANCH: {new_branch}"
                    elif layout.btn_export.check_hover(mouse_pos):
                        if state.current_analysis:
                            path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
                            if path:
                                try:
                                    temp_img = "temp_plot_export.png"
                                    if state.current_plot: pygame.image.save(state.current_plot, temp_img)
                                    export_to_report(path, state.current_analysis, state.active_branch, temp_img)
                                    if os.path.exists(temp_img): os.remove(temp_img)
                                    state.status_msg = "REPORT GENERATED."
                                except Exception as e: state.status_msg = f"ERROR: {e}"
                    
                    # TREE INTERACTION
                    if not state.is_editing_metadata and not state.show_axis_selector:
                        if state.is_editing_metadata:
                             pass 
                        else:
                            selected_list = tree_ui.handle_click(event.pos, (20, 80, 800, 600))
                            if selected_list: 
                                task_manager.add_task(worker_ctrl.worker_load_experiment, [selected_list])
            
            # SPLASH / ONBOARDING
            elif current_state == STATE_SPLASH:
                if not state.show_login_box:
                    if layout.btn_new.check_hover(mouse_pos):
                        path = filedialog.askdirectory()
                        if path:
                            state.selected_project_path = path
                            init_project(path)
                            load_database_safe(os.path.join(path, "project_vault.db"))
                            state.show_login_box = True
                    elif layout.btn_load.check_hover(mouse_pos):
                        path = filedialog.askdirectory()
                        if path:
                            if os.path.exists(os.path.join(path, "project_vault.db")):
                                state.selected_project_path = path
                                load_database_safe(os.path.join(path, "project_vault.db"))
                                state.show_login_box = True
                    elif layout.btn_import.check_hover(mouse_pos):
                        file_path = filedialog.askopenfilename(filetypes=[("DB", "*.db")])
                        if file_path:
                            state.selected_project_path = os.path.dirname(file_path)
                            load_database_safe(file_path)
                            state.show_login_box = True
                else:
                    if layout.btn_confirm.check_hover(mouse_pos):
                        if len(state.researcher_name) >= 2:
                            watcher = start_watcher(os.path.join(state.selected_project_path, "data"), event_queue)
                            tree_data = db.get_tree_data()
                            if not tree_data: current_state = STATE_ONBOARDING
                            else: 
                                tree_ui.update_tree(tree_data)
                                current_state = STATE_DASHBOARD

            elif current_state == STATE_ONBOARDING:
                if layout.btn_onboard_upload.check_hover(mouse_pos):
                    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
                    if path:
                        task_manager.add_task(worker_ctrl.worker_process_new_file, [path, None, "main", state.researcher_name])
                        current_state = STATE_DASHBOARD
                elif layout.btn_skip_onboarding.check_hover(mouse_pos): current_state = STATE_DASHBOARD

        # --- KEYBOARD (Global) ---
        if event.type == pygame.KEYDOWN:
            if current_state == STATE_SPLASH and state.show_login_box:
                if event.key == pygame.K_BACKSPACE: state.researcher_name = state.researcher_name[:-1]
                else: state.researcher_name += event.unicode
            elif state.search_active:
                if event.key == pygame.K_BACKSPACE: state.search_text = state.search_text[:-1]
                else: state.search_text += event.unicode
                tree_ui.search_filter = state.search_text
            elif state.is_editing_metadata:
                if event.key == pygame.K_BACKSPACE:
                    state.meta_input_notes = state.meta_input_notes[:-1]
                else:
                    if event.unicode.isprintable():
                        state.meta_input_notes += event.unicode
        
        # --- VIEWPORT NAVIGATION ---
        if current_state == STATE_DASHBOARD:
            if event.type == pygame.MOUSEWHEEL: 
                if mouse_pos[0] > 840: # Over right panel
                    state.analysis_scroll_y = max(0, state.analysis_scroll_y - event.y * 20)
                else:
                    tree_ui.handle_zoom("in" if event.y > 0 else "out")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: tree_ui.is_panning = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2: tree_ui.is_panning = False
            if event.type == pygame.MOUSEMOTION and tree_ui.is_panning: tree_ui.camera_offset += pygame.Vector2(event.rel)

    # --- DRAWING ---
    if current_state == STATE_SPLASH:
        render_engine.draw_splash(mouse_pos)
    elif current_state == STATE_ONBOARDING:
        render_engine.draw_onboarding(mouse_pos)
    elif current_state == STATE_EDITOR:
        render_engine.draw_editor(mouse_pos)
    elif current_state == STATE_DASHBOARD:
        if state.needs_tree_update:
            tree_ui.update_tree(db.get_tree_data())
            state.needs_tree_update = False
        render_engine.draw_dashboard(mouse_pos, tree_ui, ai_engine)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()