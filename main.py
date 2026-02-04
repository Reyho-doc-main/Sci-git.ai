import pygame
import os
import json
import pandas as pd
import threading
from queue import Queue

# Internal Modules
from settings import UITheme
from state_manager import state
from database.db_handler import DBHandler
from ui.elements import VersionTree
from ui.components import Button, draw_loading_overlay
from core.watcher import start_watcher
from engine.ai import ScienceAI
from engine.analytics import create_seaborn_surface
from core.processor import export_to_report

# --- Configuration ---
WATCH_FOLDER = "./my_experiments"
if not os.path.exists(WATCH_FOLDER): 
    os.makedirs(WATCH_FOLDER)

# --- Init Pygame ---
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("SCI-GIT // Research Version Control")

clock = pygame.time.Clock()  # <--- ADD THIS LINE HERE

# --- System Components ---
db = DBHandler()
ai_engine = ScienceAI()
tree_ui = VersionTree()
event_queue = Queue()
watcher = start_watcher(WATCH_FOLDER, event_queue)

# Fonts
font_main = pygame.font.SysFont("Consolas", 14)
font_bold = pygame.font.SysFont("Consolas", 18, bold=True)
font_tiny = pygame.font.SysFont("Consolas", 12)

# --- UI Buttons ---
btn_export = Button(850, 640, 180, 40, "GENERATE REPORT", UITheme.ACCENT_ORANGE)
btn_branch = Button(1050, 640, 180, 40, "NEW BRANCH", UITheme.NODE_BRANCH)

# --- Background Workers ---

def process_new_file_worker(file_path, parent_id, branch):
    """Handles AI analysis and DB entry for a new file."""
    try:
        state.is_processing = True
        state.status_msg = f"ANALYZING: {os.path.basename(file_path)}..."
        
        # 1. AI Analysis
        analysis_data = ai_engine.analyze_csv_data(file_path)
        
        # 2. Database Commit
        new_id = db.add_experiment(
            os.path.basename(file_path), 
            file_path, 
            analysis_data.dict(), 
            parent_id, 
            branch
        )
        
        if new_id:
            state.head_id = new_id
            state.selected_id = new_id
            state.current_analysis = analysis_data.dict()
            
            # 3. Generate Plot
            df = pd.read_csv(file_path)
            state.current_plot = create_seaborn_surface(df)
            
            state.needs_tree_update = True
            state.status_msg = f"SUCCESS: COMMITTED TO {branch.upper()}"
    except Exception as e:
        state.status_msg = f"ERROR: {str(e)}"
    finally:
        state.is_processing = False

def load_experiment_worker(exp_id):
    """Loads an existing experiment's data and plot without freezing UI."""
    try:
        state.is_processing = True
        raw = db.get_experiment_by_id(exp_id)
        if raw:
            # raw: (id, timestamp, name, file_path, analysis_json, parent_id, branch_name)
            state.current_analysis = json.loads(raw[4])
            df = pd.read_csv(raw[3])
            state.current_plot = create_seaborn_surface(df)
            state.status_msg = f"LOADED: {raw[2]}"
    except Exception as e:
        state.status_msg = "FAILED TO LOAD DATA."
    finally:
        state.is_processing = False

# --- Startup Sync ---
def sync_existing_files():
    files = sorted(
        [os.path.join(WATCH_FOLDER, f) for f in os.listdir(WATCH_FOLDER) if f.endswith(".csv")],
        key=os.path.getctime
    )
    for path in files:
        if not db.get_id_by_path(path):
            event_queue.put({"type": "NEW_FILE", "path": path})

sync_existing_files()
tree_ui.update_tree(db.get_tree_data())

# --- Main Loop ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # 1. Handle Background Events
    if not event_queue.empty() and not state.is_processing:
        event = event_queue.get()
        if event["type"] == "NEW_FILE":
            threading.Thread(
                target=process_new_file_worker, 
                args=(event["path"], state.head_id, state.active_branch),
                daemon=True
            ).start()

    # 2. UI Updates
    if state.needs_tree_update:
        tree_ui.update_tree(db.get_tree_data())
        state.needs_tree_update = False

    # 3. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and not state.is_processing:
            # Check Tree Clicks
            clicked_id = tree_ui.handle_click(event.pos, (20, 80, 800, 600))
            if clicked_id:
                state.selected_id = clicked_id
                threading.Thread(target=load_experiment_worker, args=(clicked_id,), daemon=True).start()

            # Check Button Clicks
            if btn_export.check_hover(mouse_pos) and state.current_analysis:
                report_name = f"report_exp_{state.selected_id}.pdf"
                export_to_report(report_name, state.current_analysis, state.active_branch)
                state.status_msg = f"EXPORTED: {report_name}"

            if btn_branch.check_hover(mouse_pos):
                # Simple branch toggle for hackathon demo
                state.active_branch = "dev_branch" if state.active_branch == "main" else "main"
                state.status_msg = f"SWITCHED TO BRANCH: {state.active_branch}"

    # 4. Rendering
    screen.fill(UITheme.BG_DARK)
    UITheme.draw_grid(screen)
    
    # --- Header ---
    pygame.draw.rect(screen, UITheme.PANEL_GREY, (0, 0, 1280, 60))
    pygame.draw.line(screen, UITheme.ACCENT_ORANGE, (0, 60), (1280, 60), 2)
    
    title = font_bold.render(f"SCI-GIT // PROTOCOL: {state.active_branch.upper()}", True, UITheme.ACCENT_ORANGE)
    screen.blit(title, (20, 20))
    
    # Status Bar (Terminal Style)
    status_surf = font_main.render(f"> {state.status_msg}", True, UITheme.TEXT_DIM)
    screen.blit(status_surf, (850, 22))

    # --- Left Panel: Version Tree ---
    tree_rect = (20, 80, 800, 600)
    pygame.draw.rect(screen, UITheme.PANEL_GREY, tree_rect)
    UITheme.draw_bracket(screen, tree_rect, UITheme.ACCENT_ORANGE)
    
    # Create a sub-surface for the tree to handle clipping
    tree_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
    tree_ui.draw(tree_surf, mouse_pos)
    screen.blit(tree_surf, (20, 80))

    # --- Right Panel: Analysis & Plots ---
    side_rect = (840, 80, 420, 600)
    pygame.draw.rect(screen, UITheme.PANEL_GREY, side_rect)
    UITheme.draw_bracket(screen, side_rect, (100, 100, 100))
    
    if state.current_plot:
        # Draw plot with a small border
        plot_pos = (850, 100)
        screen.blit(state.current_plot, plot_pos)
        pygame.draw.rect(screen, (50, 50, 55), (850, 100, 400, 300), 1)
    else:
        # Placeholder for plot
        pygame.draw.rect(screen, (30, 30, 35), (850, 100, 400, 300))
        msg = font_tiny.render("NO DATA SELECTED", True, UITheme.TEXT_DIM)
        screen.blit(msg, (980, 240))
    
    # AI Summary Text
    if state.current_analysis:
        y_off = 420
        summary_title = font_bold.render("AI ANALYSIS SUMMARY", True, UITheme.NODE_MAIN)
        screen.blit(summary_title, (855, y_off))
        
        # Wrap and render the summary
        UITheme.render_terminal_text(
            screen, 
            state.current_analysis.get('summary', "No summary available."), 
            (855, y_off + 30), 
            font_main, 
            UITheme.TEXT_OFF_WHITE,
            width_limit=390
        )

    # --- Bottom Controls ---
    btn_export.check_hover(mouse_pos)
    btn_export.draw(screen, font_main)
    
    btn_branch.check_hover(mouse_pos)
    btn_branch.draw(screen, font_main)

    # --- Overlays ---
    if state.is_processing:
        draw_loading_overlay(screen, font_bold)

    pygame.display.flip()
    clock.tick(60)

# Cleanup
watcher.stop()
db.close()
pygame.quit()