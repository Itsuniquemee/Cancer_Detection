import sqlite3
from pathlib import Path


class DatabaseHelper:
    """Basic local SQLite helper class."""

    def __init__(self, db_name='cancer_detection.db'):
        self.db_path = Path(db_name)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        with self.get_connection() as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result TEXT NOT NULL,
                    confidence REAL,
                    created_at TEXT NOT NULL
                )
                '''
            )

    def save_prediction(self, result, confidence, created_at):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO predictions (result, confidence, created_at) VALUES (?, ?, ?)',
                (result, confidence, created_at),
            )
