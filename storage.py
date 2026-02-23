import sqlite3
import os

class Storage:
    def __init__(self, db_path="scout.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_issues (
                issue_id INTEGER PRIMARY KEY
            )
        """)
        conn.commit()
        conn.close()

    def is_processed(self, issue_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_issues WHERE issue_id = ?", (issue_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_processed(self, issue_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO processed_issues (issue_id) VALUES (?)", (issue_id,))
        conn.commit()
        conn.close()
