"""
Database management for the AI Language Tutor application.
Handles SQLite connections, queries, and transaction management.
"""

import sqlite3
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from datetime import datetime
import logging

from config import config
from utils.logger import get_logger, LoggerMixin


class DatabaseManager(LoggerMixin):
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection: Optional[sqlite3.Connection] = None
        self.logger.info(f"Initializing database at {self.db_path}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for SQLite compatibility."""
        sanitized = {}
        for key, value in data.items():
            if value is None:
                sanitized[key] = None
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON strings
                sanitized[key] = json.dumps(value)
            elif hasattr(value, 'isoformat'):
                # Handle datetime objects
                sanitized[key] = value.isoformat()
            else:
                # Convert other types to string
                sanitized[key] = str(value)
        return sanitized
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = self._get_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database operation failed: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0
        )
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        
        # Set busy timeout
        conn.execute("PRAGMA busy_timeout = 30000")
        
        # Configure for better performance
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        # Register JSON adapter
        sqlite3.register_adapter(dict, json.dumps)
        sqlite3.register_adapter(list, json.dumps)
        sqlite3.register_converter("JSON", json.loads)
        
        return conn
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return the cursor."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
    
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute a query multiple times with different parameters."""
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Fetch a single row."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """Fetch all rows."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def fetch_dict(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dictionary."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetch_dict_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as dictionaries."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a row and return the last row ID."""
        sanitized_data = self._sanitize_data(data)
        columns = ', '.join(sanitized_data.keys())
        placeholders = ', '.join(['?' for _ in sanitized_data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, tuple(sanitized_data.values()))
            conn.commit()
            return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        """Update rows and return the number of affected rows."""
        sanitized_data = self._sanitize_data(data)
        set_clause = ', '.join([f"{k} = ?" for k in sanitized_data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, tuple(sanitized_data.values()) + where_params)
            conn.commit()
            return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        """Delete rows and return the number of affected rows."""
        query = f"DELETE FROM {table} WHERE {where}"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, where_params)
            conn.commit()
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        return result is not None
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about table columns."""
        query = f"PRAGMA table_info({table_name})"
        return self.fetch_dict_all(query)
    
    def get_table_count(self, table_name: str) -> int:
        """Get the number of rows in a table."""
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.fetch_one(query)
        return result[0] if result else 0
    
    def vacuum(self):
        """Optimize the database."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            self.logger.info("Database vacuum completed")
    
    def analyze(self):
        """Update table statistics."""
        with self.get_connection() as conn:
            conn.execute("ANALYZE")
            self.logger.info("Database analysis completed")
    
    def backup(self, backup_path: Path):
        """Create a backup of the database."""
        import shutil
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            # Create backup
            backup_conn = sqlite3.connect(str(backup_path))
            conn.backup(backup_conn)
            backup_conn.close()
        
        self.logger.info(f"Database backup created at {backup_path}")
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self.logger.info("Database connection closed")
    
    def get_database_size(self) -> int:
        """Get the database file size in bytes."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            'file_size_bytes': self.get_database_size(),
            'file_size_mb': round(self.get_database_size() / (1024 * 1024), 2),
            'tables': {}
        }
        
        # Get table statistics
        tables_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        tables = self.fetch_all(tables_query)
        
        for (table_name,) in tables:
            count = self.get_table_count(table_name)
            stats['tables'][table_name] = {
                'row_count': count,
                'size_estimate': count * 100  # Rough estimate
            }
        
        return stats


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


