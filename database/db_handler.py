import sqlite3
import json
from datetime import datetime

class DBHandler:
    def __init__(self, db_path="research_vault.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
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
            FOREIGN KEY (parent_id) REFERENCES experiments (id)
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def get_id_by_path(self, path):
        """Checks if a file is already processed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM experiments WHERE file_path = ?", (path,))
        res = cursor.fetchone()
        return res[0] if res else None

    def add_experiment(self, name, file_path, analysis_dict, parent_id=None, branch="main"):
            # Check if it already exists first
            existing_id = self.get_id_by_path(file_path)
            if existing_id:
                return existing_id # Return existing instead of failing

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
        cursor = self.conn.cursor()
        # Important: Order by ID so parents always exist before children in our processing loop
        cursor.execute("SELECT id, parent_id, branch_name, name FROM experiments ORDER BY id ASC")
        return cursor.fetchall()

    def get_experiment_by_id(self, exp_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()