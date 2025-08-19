"""
Data models for the AI Language Tutor application.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UserProfile:
    """User profile model."""
    id: int
    name: str
    target_language: str
    native_language: str
    proficiency_level: str = "beginner"
    learning_goals: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UserNotes:
    """User notes model."""
    id: int
    category: str
    content: str
    confidence_score: float = 0.5
    evidence_count: int = 1
    last_updated: Optional[datetime] = None
    tags: Optional[List[str]] = None


@dataclass
class Vocabulary:
    """Vocabulary model."""
    id: int
    word: str
    language: str
    translation: Optional[str] = None
    definition: Optional[str] = None
    phonetic: Optional[str] = None
    part_of_speech: Optional[str] = None
    difficulty_level: int = 1
    mastery_score: float = 0.0
    review_count: int = 0
    correct_count: int = 0
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    ease_factor: float = 2.5
    interval_days: float = 1.0
    context_examples: Optional[List[str]] = None
    usage_frequency: float = 0.0
    created_at: Optional[datetime] = None


@dataclass
class LearningSession:
    """Learning session model."""
    id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    mode: str = "conversation"
    summary: Optional[str] = None
    transcript_summary: Optional[str] = None
    raw_transcript: Optional[str] = None
    vocab_practiced: Optional[List[str]] = None
    new_vocab_learned: Optional[List[str]] = None
    corrections_made: Optional[List[Dict[str, Any]]] = None
    quiz_results: Optional[Dict[str, Any]] = None
    engagement_score: float = 0.0
    difficulty_level: float = 1.0
    notes: Optional[str] = None
    archived: bool = False


@dataclass
class MediaLibrary:
    """Media library model."""
    id: str
    title: str
    type: str
    language: str
    difficulty_level: Optional[int] = None
    duration_minutes: Optional[int] = None
    url: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    recommended_at: Optional[datetime] = None
    consumed_at: Optional[datetime] = None
    user_rating: Optional[int] = None
    completion_percentage: float = 0.0
    notes: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Assessment:
    """Assessment model."""
    id: str
    type: str
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    score: float
    max_score: float
    session_id: Optional[str] = None
    time_taken_seconds: Optional[int] = None
    difficulty_level: Optional[float] = None
    areas_tested: Optional[List[str]] = None
    created_at: Optional[datetime] = None


@dataclass
class LearningMetrics:
    """Learning metrics model."""
    id: int
    metric_name: str
    metric_value: float
    metadata: Optional[Dict[str, Any]] = None
    recorded_at: Optional[datetime] = None
    session_id: Optional[str] = None


@dataclass
class Settings:
    """Settings model."""
    key: str
    value: str
    type: str = "string"
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
