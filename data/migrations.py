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
                    media_preferences TEXT,
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
                    part_of_speech TEXT,
                    difficulty_level REAL DEFAULT 1.0,
                    mastery_level REAL DEFAULT 0.0,
                    times_seen INTEGER DEFAULT 0,
                    times_used INTEGER DEFAULT 0,
                    last_reviewed TIMESTAMP,
                    next_review TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Learning sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    user_id INTEGER,
                    session_type TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    words_learned INTEGER DEFAULT 0,
                    accuracy_percentage REAL DEFAULT 0.0,
                    notes TEXT,
                    mode TEXT DEFAULT 'conversation',
                    summary TEXT,
                    vocab_practiced TEXT,
                    new_vocab_learned TEXT,
                    corrections_made TEXT,
                    engagement_score REAL DEFAULT 0.0,
                    difficulty_level REAL DEFAULT 1.0,
                    archived BOOLEAN DEFAULT 0,
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
                    category TEXT,
                    language TEXT,
                    priority INTEGER DEFAULT 1,
                    tags TEXT,
                    archived BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profile (id)
                )
            """)
            
            # Add unique constraint to prevent duplicate notes
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_notes_unique ON user_notes(title, content)
            """)
            
            # Add missing columns to learning_sessions table if they don't exist
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN mode TEXT DEFAULT 'conversation'")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN summary TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN vocab_practiced TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN new_vocab_learned TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN corrections_made TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN engagement_score REAL DEFAULT 0.0")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN difficulty_level REAL DEFAULT 1.0")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN archived BOOLEAN DEFAULT 0")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE learning_sessions ADD COLUMN session_id TEXT")
            except:
                pass  # Column already exists
                
            # Add media_preferences column to user_profile if it doesn't exist
            try:
                cursor.execute("ALTER TABLE user_profile ADD COLUMN media_preferences TEXT")
            except:
                pass  # Column already exists
                
            # Add missing columns to user_notes table if they don't exist
            try:
                cursor.execute("ALTER TABLE user_notes ADD COLUMN category TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE user_notes ADD COLUMN language TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE user_notes ADD COLUMN priority INTEGER DEFAULT 1")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE user_notes ADD COLUMN archived BOOLEAN DEFAULT 0")
            except:
                pass  # Column already exists
                
            # Add missing columns to vocabulary table if they don't exist
            try:
                cursor.execute("ALTER TABLE vocabulary ADD COLUMN part_of_speech TEXT")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE vocabulary ADD COLUMN times_seen INTEGER DEFAULT 0")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE vocabulary ADD COLUMN times_used INTEGER DEFAULT 0")
            except:
                pass  # Column already exists
                
            try:
                cursor.execute("ALTER TABLE vocabulary ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except:
                pass  # Column already exists
            
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
            
            # Conversation messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    confidence_score REAL,
                    processing_time_ms INTEGER,
                    metadata TEXT
                )
            """)
            
            # Grammar topics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grammar_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    language TEXT NOT NULL,
                    difficulty_level INTEGER DEFAULT 1,
                    description TEXT,
                    examples TEXT,
                    rules TEXT,
                    user_struggles TEXT,
                    mastery_score REAL DEFAULT 0.0,
                    last_practiced TIMESTAMP,
                    next_review TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Media recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    difficulty_level INTEGER,
                    duration_minutes INTEGER,
                    url TEXT,
                    description TEXT,
                    tags TEXT,
                    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    consumed_at TIMESTAMP,
                    user_rating INTEGER,
                    completion_percentage REAL DEFAULT 0.0,
                    notes TEXT,
                    source TEXT
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
            
            # Insert sample user notes
            try:
                cursor.execute("PRAGMA table_info(user_notes)")
                notes_cols = {row[1] for row in cursor.fetchall()}
                if {'title', 'content'}.issubset(notes_cols):
                    sample_notes = [
                        ("Russian Grammar Notes", "Remember that Russian has 6 cases: nominative, genitive, dative, accusative, instrumental, and prepositional.", "grammar"),
                        ("Vocabulary Practice", "Practice common greetings and introductions in Russian.", "vocabulary"),
                        ("Pronunciation Tips", "Focus on the rolling 'r' sound and stress patterns in Russian words.", "pronunciation")
                    ]
                    for title, content, category in sample_notes:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO user_notes (title, content, tags)
                            VALUES (?, ?, ?)
                            """,
                            (title, content, category),
                        )
                else:
                    self.logger.warning("Skipping sample user_notes insert due to schema mismatch")
            except Exception as e:
                self.logger.warning(f"Skipping sample user_notes insert due to schema mismatch: {e}")
            
            # Insert sample grammar topics
            try:
                cursor.execute("PRAGMA table_info(grammar_topics)")
                grammar_cols = {row[1] for row in cursor.fetchall()}
                if {'topic', 'language'}.issubset(grammar_cols):
                    sample_topics = [
                        ("Russian Cases", "Russian", 2, "Understanding the 6 grammatical cases in Russian"),
                        ("Verb Conjugation", "Russian", 1, "Present tense verb conjugation patterns"),
                        ("Gender Agreement", "Russian", 1, "Noun and adjective gender agreement")
                    ]
                    for topic, language, level, description in sample_topics:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO grammar_topics (topic, language, difficulty_level, description)
                            VALUES (?, ?, ?, ?)
                            """,
                            (topic, language, level, description),
                        )
                else:
                    self.logger.warning("Skipping sample grammar_topics insert due to schema mismatch")
            except Exception as e:
                self.logger.warning(f"Skipping sample grammar_topics insert due to schema mismatch: {e}")
            
            # Insert sample media recommendations
            try:
                cursor.execute("PRAGMA table_info(media_recommendations)")
                media_cols = {row[1] for row in cursor.fetchall()}
                if {'title', 'type', 'language'}.issubset(media_cols):
                    sample_media = [
                        ("Russian Folk Songs", "music", "Russian", 1, 30, "Traditional Russian folk music for beginners"),
                        ("Soviet Era Films", "movie", "Russian", 2, 120, "Classic Soviet cinema for intermediate learners"),
                        ("Russian News Podcast", "podcast", "Russian", 2, 45, "Daily news in simple Russian")
                    ]
                    for title, type_, language, level, duration, description in sample_media:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO media_recommendations (title, type, language, difficulty_level, duration_minutes, description)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (title, type_, language, level, duration, description),
                        )
                else:
                    self.logger.warning("Skipping sample media_recommendations insert due to schema mismatch")
            except Exception as e:
                self.logger.warning(f"Skipping sample media_recommendations insert due to schema mismatch: {e}")
            
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
