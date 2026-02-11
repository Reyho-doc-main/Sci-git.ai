# --- FILE: main.py ---
import pygame
import os
import sys
import shutil
import pathlib
import pandas as pd
import tkinter as tk
from tkinter import filedialog, simpledialog
from queue import Queue

# --- MODULES ---
from state_manager import state
from database.db_handler import DBHandler
from ui.elements import VersionTree
from ui.layout import layout
from ui.screens import RenderEngine
from core.watcher import start_watcher
from engine.ai import ScienceAI
from core.processor import export_to_report
from core.workers import TaskQueue, WorkerController
from core.hashing import save_to_vault, get_file_hash
from ui.axis_and_settings import AxisSelector, SettingsMenu 

# --- INIT ---
pygame.init()
root = tk.Tk()
root.withdraw() 
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("SCI-GIT // Research Version Control")

# --- ICON SETUP ---
try:
    if os.path.exists("image/logo.jpg"):
        icon_surf = pygame.image.load("image/logo.jpg")
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
worker_ctrl = None 

# --- NEW: Menu Objects ---
axis_selector = AxisSelector()
settings_menu = SettingsMenu()

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
    
    # Prune Missing Files on Load
    if db.prune_missing_files():
        print("Database pruned of missing files.")
        
    worker_ctrl = WorkerController(db, ai_engine) 

def clear_pycache():
    """Recursively deletes __pycache__ folders."""
    root_path = pathlib.Path(".")
    count = 0
    for p in root_path.rglob("__pycache__"):
        try:
            shutil.rmtree(p)
            count += 1
        except Exception as e:
            print(f"Failed to delete {p}: {e}")
    print(f"Cleared {count} __pycache__ folders.")

def save_editor_changes():
    if not state.selected_ids: return
    
    if state.editor_selected_cell:
        r, c = state.editor_selected_cell
        try:
            val = float(state.editor_input_buffer)
            state.editor_df.iloc[r, c] = val
        except ValueError:
            state.editor_df.iloc[r, c] = state.editor_input_buffer
        state.editor_selected_cell = None

    state.status_msg = "SAVING & VERSIONING..."
    state.processing_mode = "LOCAL"
    
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
    state.processing_mode = "LOCAL"
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
    state.processing_mode = "LOCAL"
    task_manager.add_task(worker_ctrl.worker_redo, [node_id, raw[3], state.selected_project_path, redo_hash])

def open_editor_for_selected():
    global current_state
    if len(state.selected_ids) != 1:
        state.status_msg = "SELECT 1 FILE TO EDIT"
        return
    raw = db.get_experiment_by_id(state.selected_ids[0])
    if not raw:
        state.status_msg = "ERROR: FILE NOT FOUND"
        return
    state.editor_file_path = raw[3]
    try:
        state.editor_df = pd.read_csv(state.editor_file_path)
        current_state = STATE_EDITOR
        state.editor_selected_cell = None
        state.status_msg = "EDITING MODE ACTIVE"
    except Exception:
        state.status_msg = "ERROR OPENING FILE"

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
             if "RESTORED" in state.status_msg and state.selected_ids:
                 state.processing_mode = "LOCAL"
                 task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids])
                 state.status_msg = "READY."
    
    if not event_queue.empty() and not state.is_processing and worker_ctrl:
        ev = event_queue.get()
        if ev["type"] == "NEW_FILE":
            state.processing_mode = "LOCAL"
            task_manager.add_task(worker_ctrl.worker_process_new_file, [ev["path"], state.head_id, state.active_branch, state.researcher_name])

    search_bar_hitbox = pygame.Rect(850, 45, 200, 20)

    for event in events:
        if event.type == pygame.QUIT: running = False
        
        # --- AI STOP HANDLER ---
        if state.is_processing and state.processing_mode == "AI":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if layout.btn_ai_stop.check_hover(mouse_pos):
                    state.stop_ai_requested = True
                    state.is_processing = False 
                    state.processing_mode = "NORMAL"
                    state.status_msg = "AI ABORTED."
                    continue 

        # --- EDITOR KEYBOARD INPUT ---
        if current_state == STATE_EDITOR and event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                if state.editor_selected_cell:
                    r, c = state.editor_selected_cell
                    try: state.editor_df.iloc[r, c] = float(state.editor_input_buffer)
                    except: state.editor_df.iloc[r, c] = state.editor_input_buffer
                
                if not state.editor_selected_cell:
                    new_r, new_c = 0, 0
                else:
                    r, c = state.editor_selected_cell
                    new_r, new_c = r, c
                    if event.key == pygame.K_UP: new_r = max(0, r - 1)
                    elif event.key == pygame.K_DOWN: new_r = min(len(state.editor_df)-1, r + 1)
                    elif event.key == pygame.K_LEFT: new_c = max(0, c - 1)
                    elif event.key == pygame.K_RIGHT: new_c = min(len(state.editor_df.columns)-1, c + 1)
                
                state.editor_selected_cell = (new_r, new_c)
                state.editor_input_buffer = str(state.editor_df.iloc[new_r, new_c])
                
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
                # --- SETTINGS OVERLAY ---
                if state.show_settings:
                    action = settings_menu.handle_click(mouse_pos)
                    if action == "CLEAR_CACHE":
                        clear_pycache()
                        state.status_msg = "CACHE CLEARED."
                    continue # Block other clicks

                if search_bar_hitbox.collidepoint(mouse_pos):
                    state.search_active = True
                else:
                    state.search_active = False

                if state.show_ai_popup:
                    if layout.btn_popup_close.check_hover(mouse_pos):
                        state.show_ai_popup = False
                    elif layout.btn_popup_download.check_hover(mouse_pos):
                        if state.ai_popup_data:
                            path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
                            if path:
                                try:
                                    temp_img = "temp_plot_export.png"
                                    if state.current_plot:
                                        pygame.image.save(state.current_plot, temp_img)
                                    export_to_report(path, state.ai_popup_data, "AI_SUMMARY_EXPORT", temp_img if os.path.exists(temp_img) else None)
                                    if os.path.exists(temp_img):
                                        os.remove(temp_img)
                                    state.status_msg = "PDF SAVED."
                                except Exception as e:
                                    state.status_msg = f"ERROR: {e}"
                
                elif state.show_axis_selector:
                    # Use the new AxisSelector class logic
                    axis_selector.handle_click(mouse_pos, state.plot_context, worker_ctrl, task_manager)

                elif state.show_conversion_dialog:
                    if layout.btn_conv_yes.check_hover(mouse_pos):
                        file_path, col, unit = state.pending_conversion
                        state.processing_mode = "LOCAL"
                        task_manager.add_task(worker_ctrl.worker_perform_conversion, [file_path, col, unit, state.selected_ids])
                        state.show_conversion_dialog = False
                    elif layout.btn_conv_no.check_hover(mouse_pos):
                        state.show_conversion_dialog = False

                else:
                    # --- SETTINGS BUTTON ---
                    if layout.btn_main_settings.check_hover(mouse_pos):
                        state.show_settings = True
                        continue

                    # --- NEW DROPDOWN HANDLING ---
                    
                    # 1. FILE DROPDOWN
                    if layout.btn_menu_file.check_hover(mouse_pos):
                        state.show_file_dropdown = not state.show_file_dropdown
                        state.show_edit_dropdown = False
                        state.show_ai_dropdown = False
                        continue
                    
                    if state.show_file_dropdown:
                        if layout.dd_file_export.check_hover(mouse_pos):
                            state.show_file_dropdown = False
                            state.processing_mode = "LOCAL"
                            task_manager.add_task(worker_ctrl.worker_export_project, [state.selected_project_path])
                            continue
                        # Close if clicked outside
                        if not pygame.Rect(20, 66, 140, 26).collidepoint(mouse_pos):
                            state.show_file_dropdown = False

                    # 2. EDIT DROPDOWN
                    if layout.btn_menu_edit.check_hover(mouse_pos):
                        state.show_edit_dropdown = not state.show_edit_dropdown
                        state.show_file_dropdown = False
                        state.show_ai_dropdown = False
                        continue 

                    if state.show_edit_dropdown:
                        if layout.dd_edit_undo.check_hover(mouse_pos):
                            state.show_edit_dropdown = False
                            perform_undo()
                            continue
                        if layout.dd_edit_redo.check_hover(mouse_pos):
                            state.show_edit_dropdown = False
                            perform_redo()
                            continue
                        if layout.dd_edit_file.check_hover(mouse_pos):
                            state.show_edit_dropdown = False
                            open_editor_for_selected()
                            continue
                        
                        # Close if clicked outside
                        if not pygame.Rect(90, 66, 110, 78).collidepoint(mouse_pos):
                            state.show_edit_dropdown = False

                    # 3. AI DROPDOWN
                    if layout.btn_menu_ai.check_hover(mouse_pos):
                        state.show_ai_dropdown = not state.show_ai_dropdown
                        state.show_file_dropdown = False
                        state.show_edit_dropdown = False
                        continue
                        
                    if state.show_ai_dropdown:
                        if layout.dd_ai_analyze.check_hover(mouse_pos):
                            state.show_ai_dropdown = False
                            state.processing_mode = "AI"
                            if len(state.selected_ids) == 1:
                                state.status_msg = "ANALYZING FILE (MINI)..."
                                task_manager.add_task(worker_ctrl.worker_analyze_selection, [state.selected_ids[0]])
                            else:
                                state.status_msg = "ANALYZING BRANCH (NANO)..."
                                task_manager.add_task(worker_ctrl.worker_analyze_branch, [state.active_branch])
                            continue
                        
                        if not pygame.Rect(160, 66, 140, 26).collidepoint(mouse_pos):
                            state.show_ai_dropdown = False

                    # Toggle Axis Selector
                    if layout.btn_axis_gear.check_hover(mouse_pos): 
                        state.show_axis_selector = not state.show_axis_selector
                    
                    if len(state.selected_ids) == 1 and layout.btn_add_manual.check_hover(mouse_pos):
                        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
                        if path: 
                            state.processing_mode = "LOCAL"
                            task_manager.add_task(worker_ctrl.worker_process_new_file, [path, state.selected_ids[0], state.active_branch, state.researcher_name])
                    
                    elif len(state.selected_ids) == 1 and layout.btn_edit_meta.check_hover(mouse_pos): 
                        state.is_editing_metadata = not state.is_editing_metadata
                    
                    elif state.is_editing_metadata and layout.btn_save_meta.check_hover(mouse_pos):
                        db.update_metadata(state.selected_ids[0], state.meta_input_notes)
                        state.is_editing_metadata = False
                        state.processing_mode = "LOCAL"
                        task_manager.add_task(worker_ctrl.worker_load_experiment, [state.selected_ids])
                    
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
                        selected_list = tree_ui.handle_click(event.pos, (20, 80, 800, 600))
                        if selected_list: 
                            state.processing_mode = "LOCAL"
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
                    
                    # Note: Clear Cache button removed from here, moved to Settings

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
                        state.processing_mode = "LOCAL"
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
                elif event.key == pygame.K_RETURN: state.search_active = False 
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
            if event.type == pygame.MOUSEWHEEL and state.show_ai_popup:
                state.ai_popup_scroll_y = max(0, state.ai_popup_scroll_y - event.y * 30)
                continue 
            if event.type == pygame.MOUSEWHEEL: 
                if mouse_pos[0] > 840: 
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

        # Draw New Overlays
        if state.show_axis_selector:
            axis_selector.draw(screen, 850, 130, state.plot_context)
        
        if state.show_settings:
            settings_menu.draw(screen)
            
        # Draw Settings Button Icon (if image exists, else fallback to text)
        if render_engine.icons.get('settings'):
            r = layout.btn_main_settings.rect
            screen.blit(render_engine.icons['settings'], (r.x, r.y))
        else:
            layout.btn_main_settings.draw(screen, render_engine.font_bold)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()