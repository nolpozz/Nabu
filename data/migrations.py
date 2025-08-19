"""
Database migrations for the AI Language Tutor application.
Handles schema creation and updates.
"""

import sqlite3
from typing import List, Dict, Any
from utils.logger import get_logger


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = get_logger(__name__)
    
    def create_schema(self):
        """Create the initial database schema."""
        self.logger.info("Creating database schema")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User profile table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    native_language TEXT,
                    target_languages TEXT,
                    proficiency_level TEXT,
                    learning_goals TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Vocabulary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    word TEXT NOT NULL,
                    translation TEXT,
                    language TEXT NOT NULL,
                    difficulty_level INTEGER DEFAULT 1,
                    mastery_level INTEGER DEFAULT 0,
                    last_reviewed TIMESTAMP,
                    next_review TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Learning sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_type TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    words_learned INTEGER DEFAULT 0,
                    accuracy_percentage REAL DEFAULT 0.0,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    user_message TEXT,
                    ai_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language TEXT,
                    FOREIGN KEY (session_id) REFERENCES learning_sessions (id)
                )
            """)
            
            # Grammar rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grammar_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    rule_description TEXT,
                    examples TEXT,
                    difficulty_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Progress tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS progress_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Media resources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    difficulty_level INTEGER DEFAULT 1,
                    url TEXT,
                    description TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    content TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Assessment results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    assessment_type TEXT NOT NULL,
                    score REAL,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            conn.commit()
            self.logger.info("Database schema created successfully")
    
    def insert_sample_data(self):
        """Insert sample data for testing."""
        self.logger.info("Inserting sample data")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Detect existing columns to avoid insert errors on legacy DBs
            cursor.execute("PRAGMA table_info(user_profile)")
            user_profile_cols = {row[1] for row in cursor.fetchall()}
            
            # Insert sample user
            try:
                if 'username' in user_profile_cols:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO user_profile (username, email, native_language, target_languages, proficiency_level)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        ("testuser", "test@example.com", "English", "Spanish,French", "Intermediate"),
                    )
                elif 'name' in user_profile_cols:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO user_profile (name, email, native_language, target_languages, proficiency_level)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        ("testuser", "test@example.com", "English", "Spanish,French", "Intermediate"),
                    )
                else:
                    # Minimal insert if schema is very old
                    minimal_cols = [c for c in ['email'] if c in user_profile_cols]
                    if minimal_cols:
                        placeholders = ", ".join(minimal_cols)
                        values = tuple(["test@example.com"]) if 'email' in minimal_cols else tuple()
                        cursor.execute(
                            f"INSERT OR IGNORE INTO user_profile ({placeholders}) VALUES ({', '.join(['?']*len(values))})",
                            values,
                        )
            except Exception as e:
                self.logger.warning(f"Skipping sample user insert due to schema mismatch: {e}")
            
            # Insert sample vocabulary (only if schema supports it)
            try:
                cursor.execute("PRAGMA table_info(vocabulary)")
                vocab_cols = {row[1] for row in cursor.fetchall()}
                required_cols = {'word', 'language'}
                if required_cols.issubset(vocab_cols):
                    sample_words = [
                        ("hola", "hello", "Spanish", 1),
                        ("gracias", "thank you", "Spanish", 1),
                        ("bonjour", "hello", "French", 1),
                        ("merci", "thank you", "French", 1),
                        ("casa", "house", "Spanish", 2),
                        ("maison", "house", "French", 2)
                    ]
                    for word, translation, language, level in sample_words:
                        if {'user_id','translation','difficulty_level'}.issubset(vocab_cols):
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO vocabulary (user_id, word, translation, language, difficulty_level)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (1, word, translation, language, level),
                            )
                        elif {'translation'}.issubset(vocab_cols):
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO vocabulary (word, translation, language)
                                VALUES (?, ?, ?)
                                """,
                                (word, translation, language),
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO vocabulary (word, language)
                                VALUES (?, ?)
                                """,
                                (word, language),
                            )
                else:
                    self.logger.warning("Skipping sample vocabulary insert due to schema mismatch (missing required columns)")
            except Exception as e:
                self.logger.warning(f"Skipping sample vocabulary insert due to schema mismatch: {e}")
            
            # Insert sample session with column checks
            try:
                cursor.execute("PRAGMA table_info(learning_sessions)")
                session_cols = {row[1] for row in cursor.fetchall()}
                base_values = {
                    'session_type': 'conversation',
                    'duration_seconds': 900,
                    'words_learned': 15,
                    'accuracy_percentage': 85.5,
                }
                available_cols = [c for c in base_values.keys() if c in session_cols]
                if 'user_id' in session_cols:
                    available_cols = ['user_id'] + available_cols
                    values = [1] + [base_values[c] for c in available_cols if c != 'user_id']
                else:
                    values = [base_values[c] for c in available_cols]
                if available_cols:
                    placeholders = ', '.join(available_cols)
                    qs = ', '.join(['?'] * len(values))
                    cursor.execute(
                        f"INSERT OR IGNORE INTO learning_sessions ({placeholders}) VALUES ({qs})",
                        tuple(values),
                    )
                else:
                    self.logger.warning("Skipping sample learning_sessions insert due to schema mismatch (no usable columns)")
            except Exception as e:
                self.logger.warning(f"Skipping sample learning_sessions insert due to schema mismatch: {e}")
            
            conn.commit()
            self.logger.info("Sample data inserted successfully")


def run_migrations(db_or_manager, create_sample_data: bool = True):
    """Run all database migrations.

    Accepts either a path to the database file or a DatabaseManager-like
    object that has a `db_path` attribute. This matches existing usage in
    the application where a `DatabaseManager` instance is passed.
    """
    logger = get_logger(__name__)

    # Resolve db_path from either a string/path or a manager with db_path
    try:
        db_path = getattr(db_or_manager, 'db_path', db_or_manager)
    except Exception:
        db_path = db_or_manager

    db_path_str = str(db_path)
    logger.info(f"Running migrations for database: {db_path_str}")

    migration_manager = MigrationManager(db_path_str)
    migration_manager.create_schema()

    if create_sample_data:
        migration_manager.insert_sample_data()

    logger.info("Migrations completed successfully")
