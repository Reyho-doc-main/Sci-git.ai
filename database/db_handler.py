# --- FILE: database/db_handler.py ---
import sqlite3
import json
import threading
import os
from datetime import datetime

class DBHandler:
    def __init__(self, db_path="research_vault.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS node_history (node_id INTEGER, file_hash TEXT, timestamp DATETIME)")
        query = """
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            name TEXT,
            file_path TEXT UNIQUE,
            analysis_json TEXT,
            parent_id INTEGER,
            branch_name TEXT,
            researcher_name TEXT DEFAULT 'ANONYMOUS',
            notes TEXT,
            temperature TEXT,
            sample_id TEXT,
            plot_settings TEXT,
            FOREIGN KEY (parent_id) REFERENCES experiments (id)
        )
        """
        with self.lock:
            self.conn.execute(query)
            self.conn.commit()

            # Migration helper
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(experiments)")
            columns = [info[1] for info in cursor.fetchall()]

            if "plot_settings" not in columns:
                try:
                    self.conn.execute("ALTER TABLE experiments ADD COLUMN plot_settings TEXT")
                    self.conn.commit()
                except sqlite3.Error:
                    pass
                    
            if "linked_nodes" not in columns:
                try:
                    self.conn.execute("ALTER TABLE experiments ADD COLUMN linked_nodes TEXT")
                    self.conn.commit()
                except sqlite3.Error:
                    pass

    def get_id_by_path(self, path):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM experiments WHERE file_path = ?", (path,))
            res = cursor.fetchone()
            return res[0] if res else None

    def add_experiment(self, name, file_path, analysis_dict, parent_id=None, branch="main"):
        existing_id = self.get_id_by_path(file_path)
        if existing_id: return existing_id

        query = """
        INSERT INTO experiments (timestamp, name, file_path, analysis_json, parent_id, branch_name)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(query, (
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    name,
                    file_path,
                    json.dumps(analysis_dict),
                    parent_id,
                    branch
                ))
                self.conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM experiments WHERE file_path = ?", (file_path,))
                res = cursor.fetchone()
                return res[0] if res else None

    def get_tree_data(self):
        """Returns hierarchical experiment relationships and additional links."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, parent_id, branch_name, name, linked_nodes FROM experiments ORDER BY id ASC")
            return cursor.fetchall()

    def get_experiment_by_id(self, exp_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
            return cursor.fetchone()

    def update_metadata(self, exp_id, notes):
        query = "UPDATE experiments SET notes = ? WHERE id = ?"
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, (notes, exp_id))
            self.conn.commit()

    def update_plot_settings(self, exp_id, x_col, y_col):
        settings = json.dumps({"x": x_col, "y": y_col})
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE experiments SET plot_settings = ? WHERE id = ?", (settings, exp_id))
            self.conn.commit()
            
    def add_linkage(self, source_id, target_id):
        """Adds a custom visual linkage connection between nodes."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT linked_nodes FROM experiments WHERE id = ?", (source_id,))
            res = cursor.fetchone()
            links = []
            if res and res[0]:
                try: links = json.loads(res[0])
                except: pass
            if target_id not in links:
                links.append(target_id)
            cursor.execute("UPDATE experiments SET linked_nodes = ? WHERE id = ?", (json.dumps(links), source_id))
            self.conn.commit()

    def close(self):
        try:
            with self.lock:
                self.conn.close()
        except sqlite3.Error:
            pass

    def add_hash_to_history(self, node_id, file_hash):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_hash FROM node_history WHERE node_id = ? ORDER BY rowid DESC LIMIT 1", (node_id,))
            last = cursor.fetchone()
            if not last or last[0] != file_hash:
                cursor.execute("INSERT INTO node_history (node_id, file_hash, timestamp) VALUES (?, ?, ?)", 
                               (node_id, file_hash, datetime.now()))
                self.conn.commit()

    def get_node_history(self, node_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_hash FROM node_history WHERE node_id = ? ORDER BY rowid ASC", (node_id,))
            return [r[0] for r in cursor.fetchall()]
            
    def remove_last_history_entry(self, node_id):
        with self.lock:
            cursor = self.conn.cursor()
            query = "DELETE FROM node_history WHERE rowid = (SELECT rowid FROM node_history WHERE node_id = ? ORDER BY rowid DESC LIMIT 1)"
            cursor.execute(query, (node_id,))
            self.conn.commit()
            
    def prune_missing_files(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, file_path FROM experiments")
            rows = cursor.fetchall()
            removed = False
            for exp_id, file_path in rows:
                if file_path and not os.path.exists(file_path):
                    cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
                    removed = True
            if removed:
                self.conn.commit()
            return removed