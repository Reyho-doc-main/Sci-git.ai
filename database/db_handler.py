import sqlite3
import json
from datetime import datetime

class DBHandler:
    def __init__(self, db_path="research_vault.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # Unified schema
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
        self.conn.execute(query)
        self.conn.commit()

        # Migration helper: ensure plot_settings exists
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(experiments)")
        columns = [info[1] for info in cursor.fetchall()]

        if "plot_settings" not in columns:
            try:
                self.conn.execute("ALTER TABLE experiments ADD COLUMN plot_settings TEXT")
                self.conn.commit()
            except sqlite3.Error:
                pass

    def get_id_by_path(self, path):
        """Checks if a file is already processed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM experiments WHERE file_path = ?", (path,))
        res = cursor.fetchone()
        return res[0] if res else None

    def add_experiment(self, name, file_path, analysis_dict, parent_id=None, branch="main"):
        """Adds a new experiment record, avoiding duplicates."""
        existing_id = self.get_id_by_path(file_path)
        if existing_id:
            return existing_id

        query = """
        INSERT INTO experiments (timestamp, name, file_path, analysis_json, parent_id, branch_name)
        VALUES (?, ?, ?, ?, ?, ?)
        """
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
            return self.get_id_by_path(file_path)

    def get_tree_data(self):
        """Returns hierarchical experiment relationships."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, parent_id, branch_name, name FROM experiments ORDER BY id ASC")
        return cursor.fetchall()

    def get_experiment_by_id(self, exp_id):
        """Fetches full experiment record by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
        return cursor.fetchone()

    def update_metadata(self, exp_id, notes, temp, sample_id):
        """Saves scientist's manual edits to metadata fields."""
        query = """
        UPDATE experiments 
        SET notes = ?, temperature = ?, sample_id = ? 
        WHERE id = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (notes, temp, sample_id, exp_id))
        self.conn.commit()

    def update_plot_settings(self, exp_id, x_col, y_col):
        """Persists the user's axis selection for plotting."""
        settings = json.dumps({"x": x_col, "y": y_col})
        cursor = self.conn.cursor()
        cursor.execute("UPDATE experiments SET plot_settings = ? WHERE id = ?", (settings, exp_id))
        self.conn.commit()

    def close(self):
        """Safely closes the database connection."""
        try:
            self.conn.close()
        except sqlite3.Error:
            pass