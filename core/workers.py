import pygame
import os
import json
import pandas as pd
import threading
import shutil
from queue import Queue
from state_manager import state
from engine.analytics import create_seaborn_surface, HeaderScanner
from core.hashing import save_to_vault, get_file_hash, ensure_vault

class WorkerController:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai_engine = ai_engine

    def worker_load_experiment(self, exp_ids, custom_x=None, custom_y=None, save_settings=False):
        try:
            if len(exp_ids) == 1:
                raw = self.db.get_experiment_by_id(exp_ids[0])
                if raw:
                    file_path = raw[3]

                    if not os.path.exists(file_path):
                        return {
                            "type": "LOAD_COMPLETE",
                            "data": {
                                "analysis": {"summary": "CRITICAL ERROR: The source CSV file for this node has been moved or deleted.", "anomalies": ["FILE_NOT_FOUND"]},
                                "status": "FILE MISSING",
                                "is_corrupted": True
                            }
                        }
                    saved_settings = None
                    if len(raw) > 11 and raw[11]: saved_settings = json.loads(raw[11])
                    final_x = custom_x if custom_x else (saved_settings.get("x") if saved_settings else None)
                    final_y = custom_y if custom_y else (saved_settings.get("y") if saved_settings else None)

                    if save_settings and final_x and final_y: 
                        self.db.update_plot_settings(exp_ids[0], final_x, final_y)

                    file_size = os.path.getsize(file_path)
                    if file_size > 50 * 1024 * 1024: # 50MB
                        df = pd.read_csv(file_path, nrows=1000)
                        status_note = "LARGE FILE: PREVIEW MODE (FIRST 1000 ROWS)"
                    else:
                        df = pd.read_csv(file_path)
                        status_note = f"LOADED: {raw[2]}"

                    plot_bytes, size, context = create_seaborn_surface(df, x_col=final_x, y_col=final_y)
                    
                    return {
                        "type": "LOAD_COMPLETE",
                        "data": {
                            "plot_data": (plot_bytes, size, context),
                            "analysis": json.loads(raw[4]),
                            "metadata": {"notes": raw[8]},
                            "status": status_note
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

    def worker_save_editor_changes(self, node_id, file_path, df, project_path):
        """Saves editor changes with version control (hashing old version)."""
        try:
            # 1. Archive the current version on disk before overwriting
            old_hash = save_to_vault(file_path, project_path)
            if old_hash:
                self.db.add_hash_to_history(node_id, old_hash)
            
            # 2. Save the new data
            df.to_csv(file_path, index=False)
            
            # 3. Reload visualization
            return {
                "type": "SAVE_COMPLETE", 
                "data": {"node_id": node_id, "status": "VERSION SAVED"}
            }
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_undo(self, node_id, file_path, project_path, redo_stack_list):
        """Reverts file to previous hash, pushes current to Redo stack."""
        try:
            history = self.db.get_node_history(node_id)
            if not history:
                return {"type": "ERROR", "data": "NO HISTORY TO UNDO"}
            
            # The last item in history is the state *before* the current file state
            target_hash = history[-1]
            vault_file = os.path.join(project_path, ".sci_vault", f"{target_hash}.csv")
            
            if not os.path.exists(vault_file):
                return {"type": "ERROR", "data": "VERSION MISSING IN VAULT"}

            # 1. Save CURRENT state to Vault for Redo
            current_hash = save_to_vault(file_path, project_path)
            
            # 2. Restore Old File
            shutil.copy2(vault_file, file_path)
            
            # 3. Update DB (Remove used history) and return data for Redo Stack
            self.db.remove_last_history_entry(node_id)
            
            return {
                "type": "UNDO_COMPLETE",
                "data": {
                    "node_id": node_id,
                    "redo_hash": current_hash,
                    "restored_hash": target_hash
                }
            }
        except Exception as e:
            return {"type": "ERROR", "data": str(e)}

    def worker_redo(self, node_id, file_path, project_path, redo_hash):
        try:
            vault_file = os.path.join(project_path, ".sci_vault", f"{redo_hash}.csv")
            if not os.path.exists(vault_file):
                 return {"type": "ERROR", "data": "REDO TARGET MISSING"}
            
            # 1. Save CURRENT state (which was the 'Undo' state) back to history
            current_hash = save_to_vault(file_path, project_path)
            if current_hash:
                self.db.add_hash_to_history(node_id, current_hash)
                
            # 2. Restore the Redo file
            shutil.copy2(vault_file, file_path)
            
            return {
                "type": "REDO_COMPLETE",
                "data": {"node_id": node_id, "restored_hash": redo_hash}
            }
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

            elif msg_type == "SAVE_COMPLETE":
                # Clear Redo stack on new save (divergent history)
                if 'node_id' in data:
                    state.redo_stack[data['node_id']] = [] 
                state.status_msg = "VERSION SAVED."
                state.is_processing = False

            elif msg_type == "UNDO_COMPLETE":
                node_id = data['node_id']
                if node_id not in state.redo_stack: state.redo_stack[node_id] = []
                state.redo_stack[node_id].append(data['redo_hash'])
                state.status_msg = f"UNDO: RESTORED {data['restored_hash'][:8]}"
                state.is_processing = False
            
            elif msg_type == "REDO_COMPLETE":
                state.status_msg = f"REDO: RESTORED {data['restored_hash'][:8]}"
                state.is_processing = False