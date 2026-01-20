# ==========================================
# File: src/core/db_manager.py
# ==========================================
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator
from config.settings import settings
from config.logging_config import GLOBAL_LOGGER as logger



class DBManager:
    """
    Singleton Database Manager for SQLite.
    Handles connection lifecycle and row mapping.
    """
    
    def __init__(self):
        # Ensure the directory exists
        pass 

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = None
        try:
            conn = sqlite3.connect(settings.SQL_DB_PATH)
            conn.row_factory = sqlite3.Row 
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            # CHANGED: Structured logging (no f-string needed for the message)
            logger.error("database_transaction_failed", error=str(e))
            raise e
        finally:
            if conn:
                conn.close()

    def get_cursor(self):
        """
        Helper if you just need a cursor.
        """
        return self.get_connection()

# Singleton Instance
db_manager = DBManager()