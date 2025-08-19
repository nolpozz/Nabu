"""
Data layer for the AI Language Tutor application.
Handles database operations, data models, and persistence.
"""

from .database import DatabaseManager
from .models import (
    UserProfile,
    UserNotes,
    Vocabulary,
    LearningSession,
    MediaLibrary,
    Assessment,
    LearningMetrics,
    Settings
)
from .migrations import run_migrations
from .backup_manager import BackupManager
from .analytics import AnalyticsEngine
from .user_profile import UserProfileManager
from .retention_policy import RetentionPolicy

__all__ = [
    'DatabaseManager',
    'UserProfile',
    'UserNotes', 
    'Vocabulary',
    'LearningSession',
    'MediaLibrary',
    'Assessment',
    'LearningMetrics',
    'Settings',
    'run_migrations',
    'BackupManager',
    'AnalyticsEngine',
    'UserProfileManager',
    'RetentionPolicy'
]


