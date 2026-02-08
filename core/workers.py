import pygame
import os
import json
import pandas as pd
import threading
import shutil
from queue import Queue
from state_manager import state
from engine.analytics import create_seaborn_surface, HeaderScanner

class WorkerController:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai_engine = ai_engine

    def worker_load_experiment(self, exp_ids, custom_x=None, custom_y=None, save_settings=False):
        try:
            if len(exp_ids) == 1:
                raw = self.db.get_experiment_by_id(exp_ids[0])
                if raw:
                    saved_settings = None
                    if len(raw) > 11 and raw[11]: saved_settings = json.loads(raw[11])
                    final_x = custom_x if custom_x else (saved_settings.get("x") if saved_settings else None)
                    final_y = custom_y if custom_y else (saved_settings.get("y") if saved_settings else None)
                    
                    if save_settings and final_x and final_y: 
                        self.db.update_plot_settings(exp_ids[0], final_x, final_y)

                    df = pd.read_csv(raw[3])
                    plot_bytes, size, context = create_seaborn_surface(df, x_col=final_x, y_col=final_y)
                    
                    return {
                        "type": "LOAD_COMPLETE",
                        "data": {
                            "plot_data": (plot_bytes, size, context),
                            "analysis": json.loads(raw[4]),
                            "metadata": {"notes": raw[8], "temp": raw[9], "sid": raw[10]},
                            "status": f"LOADED: {raw[2]}"
                        }
                    }
            elif len(exp_ids) == 2:
                raw1 = self.db.get_experiment_by_id(exp_ids[0])
                raw2 = self.db.get_experiment_by_id(exp_ids[1])
                if raw1 and raw2:
                    df1 = pd.read_csv(raw1[3])
                    df2 = pd.read_csv(raw2[3])
                    
                    u1, col1 = HeaderScanner.detect_temp_unit(df1)
                    u2, col2 = HeaderScanner.detect_temp_unit(df2)
                    
                    if u1 and u2 and u1 != u2:
                        return {"type": "CONVERSION_NEEDED", "data": (raw2[3], col2, u1)}
                    
                    plot_bytes, size, context = create_seaborn_surface(df1, df2, x_col=custom_x, y_col=custom_y)
                    comparison = self.ai_engine.compare_experiments(df1, df2)
                    
                    return {
                        "type": "LOAD_COMPLETE",
                        "data": {
                            "plot_data": (plot_bytes, size, context),
                            "analysis": comparison,
                            "status": "COMPARISON COMPLETE"
                        }
                    }
            return {"type": "ERROR", "data": "Invalid Selection"}
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_process_new_file(self, file_path, parent_id, branch, researcher):
        try:
            existing_id = self.db.get_id_by_path(file_path)
            if existing_id:
                return self.worker_load_experiment([existing_id])
            
            analysis_data = self.ai_engine.analyze_csv_data(file_path)
            new_id = self.db.add_experiment(os.path.basename(file_path), file_path, analysis_data.model_dump(), parent_id, branch)
            
            df = pd.read_csv(file_path)
            plot_bytes, size, context = create_seaborn_surface(df)
            
            return {
                "type": "NEW_FILE_COMPLETE",
                "data": {
                    "id": new_id,
                    "analysis": analysis_data.model_dump(),
                    "plot_data": (plot_bytes, size, context),
                    "status": f"COMMITTED BY {researcher}"
                }
            }
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_analyze_branch(self, branch_name):
        try:
            tree = self.db.get_tree_data()
            branch_nodes = [row for row in tree if row[2] == branch_name]
            history_text = "\n".join([f"ID: {row[0]} | Name: {row[3]}" for row in branch_nodes[-5:]])
            report = self.ai_engine.analyze_branch_history(history_text)
            return {
                "type": "ANALYSIS_READY",
                "data": {"summary": f"BRANCH REPORT ({branch_name}):\n{report}", "anomalies": []}
            }
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_perform_conversion(self, file_path, column, to_unit, ids_to_reload):
        try:
            df = pd.read_csv(file_path)
            df = HeaderScanner.convert_column(df, column, to_unit)
            df.to_csv(file_path, index=False)
            return self.worker_load_experiment(ids_to_reload)
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_export_project(self, project_path):
        try:
            ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
            zip_name = f"SciGit_Export_{ts}"
            output_path = os.path.join(project_path, "exports", zip_name) 
            shutil.make_archive(output_path, 'zip', project_path)
            return {"type": "EXPORT_COMPLETE", "data": f"EXPORT: {zip_name}.zip"}
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

class TaskQueue:
    def __init__(self):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _worker_loop(self):
        while True:
            func, args = self.task_queue.get()
            try:
                result = func(*args)
                self.result_queue.put(result)
            except Exception as e:
                self.result_queue.put({"type": "ERROR", "data": str(e)})
            finally:
                self.task_queue.task_done()

    def add_task(self, func, args):
        state.is_processing = True
        self.task_queue.put((func, args))

    def process_results(self):
        while not self.result_queue.empty():
            result = self.result_queue.get()
            
            if result.get("type") == "ERROR":
                state.status_msg = f"ERROR: {result['data']}"
                state.is_processing = False
                continue

            msg_type = result.get("type")
            data = result.get("data")

            if msg_type == "LOAD_COMPLETE":
                if 'plot_data' in data and data['plot_data'][0]:
                    raw, size, ctx = data['plot_data']
                    state.current_plot = pygame.image.frombuffer(raw, size, "RGBA")
                    state.plot_context = ctx
                if 'analysis' in data: state.current_analysis = data['analysis']
                if 'metadata' in data:
                    state.meta_input_notes = data['metadata'].get('notes', "") or ""
                    state.meta_input_temp = data['metadata'].get('temp', "") or ""
                    state.meta_input_sid = data['metadata'].get('sid', "") or ""
                if 'status' in data: state.status_msg = data['status']
                state.is_processing = False

            elif msg_type == "NEW_FILE_COMPLETE":
                state.head_id = data['id']
                state.selected_ids = [data['id']]
                state.current_analysis = data['analysis']
                raw, size, ctx = data['plot_data']
                state.current_plot = pygame.image.frombuffer(raw, size, "RGBA")
                state.plot_context = ctx
                state.needs_tree_update = True
                state.status_msg = data['status']
                state.is_processing = False

            elif msg_type == "CONVERSION_NEEDED":
                state.pending_conversion = data
                state.show_conversion_dialog = True
                state.is_processing = False

            elif msg_type == "ANALYSIS_READY":
                state.current_analysis = data
                state.status_msg = "ANALYSIS COMPLETE"
                state.is_processing = False
            
            elif msg_type == "EXPORT_COMPLETE":
                state.status_msg = data
                state.is_processing = False