import sqlite3
import os
from typing import List, Dict, Any
from app.config import settings
from app.observability.logging import logger

class TaskDatabaseManager:
    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH
        self._init_db()

    def _init_db(self):
        logger.info(f"Initializing SQLite Task database at: {self.db_path}")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'P1',
                    status TEXT DEFAULT 'TODO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            conn.close()
            logger.info("Task table verified/created successfully.")
        except Exception as e:
            logger.error(f"Error creating tasks SQLite database: {str(e)}", exc_info=True)

    def create_task(self, title: str, description: str, priority: str = "P1") -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, description, priority) VALUES (?, ?, ?)",
                (title, description, priority)
            )
            task_id = cursor.lastrowid or 0
            conn.commit()
            conn.close()
            logger.info(f"Created task [{task_id}]: {title} (Priority: {priority})")
            return task_id
        except Exception as e:
            logger.error(f"Failed to create task in DB: {str(e)}")
            return 0

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to read tasks from DB: {str(e)}")
            return []

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch task {task_id}: {str(e)}")
            return None

task_db_manager = TaskDatabaseManager()
