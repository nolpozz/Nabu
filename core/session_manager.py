"""
Session management for the AI Language Tutor application.
Handles learning session lifecycle, state management, and persistence.
"""

import uuid
import threading
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from utils.logger import get_logger, LoggerMixin
from data.database import DatabaseManager
from core.event_bus import EventBus, EventTypes


@dataclass
class SessionState:
    """Represents the current state of a learning session."""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    mode: str = "conversation"
    is_active: bool = True
    engagement_score: float = 0.0
    difficulty_level: float = 1.0
    vocab_practiced: List[str] = None
    new_vocab_learned: List[str] = None
    corrections_made: List[Dict[str, Any]] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.vocab_practiced is None:
            self.vocab_practiced = []
        if self.new_vocab_learned is None:
            self.new_vocab_learned = []
        if self.corrections_made is None:
            self.corrections_made = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session state to dictionary."""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        if self.ended_at:
            data['ended_at'] = self.ended_at.isoformat()
        return data


class SessionManager(LoggerMixin):
    """Manages learning sessions and their lifecycle."""
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus):
        self.db = db_manager
        self.event_bus = event_bus
        self.current_session: Optional[SessionState] = None
        self.session_history: List[SessionState] = []
        self.is_running = False
        self._lock = threading.RLock()
        
        # Background task management
        self.background_thread: Optional[threading.Thread] = None
        self.stop_background = threading.Event()
        
        # Session statistics
        self.total_sessions = 0
        self.total_duration = 0
        self.average_engagement = 0.0
        
        self.logger.info("SessionManager initialized")
    
    def start_session(self, mode: str = "conversation") -> str:
        """Start a new learning session."""
        with self._lock:
            # End current session if active
            if self.current_session and self.current_session.is_active:
                self.end_session()
            
            # Create new session
            session_id = str(uuid.uuid4())
            self.current_session = SessionState(
                session_id=session_id,
                started_at=datetime.now(),
                mode=mode
            )
            
            # Save to database
            self._save_session_to_db(self.current_session)
            
            # Publish event
            session_data = self.current_session.to_dict()
            self.event_bus.publish(EventTypes.SESSION_STARTED, session_data)
            
            self.logger.info(f"Started new session: {session_id} (mode: {mode})")
            return session_id
    
    def end_session(self, summary: str = "") -> Optional[str]:
        """End the current session."""
        with self._lock:
            if not self.current_session or not self.current_session.is_active:
                return None
            
            # Update session state
            self.current_session.ended_at = datetime.now()
            self.current_session.is_active = False
            self.current_session.duration_seconds = int(
                (self.current_session.ended_at - self.current_session.started_at).total_seconds()
            )
            if summary:
                self.current_session.notes = summary
            
            # Update database
            self._update_session_in_db(self.current_session)
            
            # Add to history
            self.session_history.append(self.current_session)
            
            # Update statistics
            self._update_statistics()
            
            # Publish event
            session_data = self.current_session.to_dict()
            self.event_bus.publish(EventTypes.SESSION_ENDED, session_data)
            
            session_id = self.current_session.session_id
            self.current_session = None
            
            self.logger.info(f"Ended session: {session_id} (duration: {session_data['duration_seconds']}s)")
            return session_id
    
    def pause_session(self) -> bool:
        """Pause the current session."""
        with self._lock:
            if not self.current_session or not self.current_session.is_active:
                return False
            
            # For now, we'll just log the pause
            # In a more complex implementation, you might want to track pause/resume times
            self.logger.info(f"Session paused: {self.current_session.session_id}")
            self.event_bus.publish(EventTypes.SESSION_PAUSED, self.current_session.to_dict())
            return True
    
    def resume_session(self) -> bool:
        """Resume the current session."""
        with self._lock:
            if not self.current_session or not self.current_session.is_active:
                return False
            
            self.logger.info(f"Session resumed: {self.current_session.session_id}")
            self.event_bus.publish(EventTypes.SESSION_RESUMED, self.current_session.to_dict())
            return True
    
    def update_session_data(self, updates: Dict[str, Any]) -> bool:
        """Update current session data."""
        with self._lock:
            if not self.current_session or not self.current_session.is_active:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(self.current_session, key):
                    setattr(self.current_session, key, value)
            
            # Update database
            self._update_session_in_db(self.current_session)
            
            self.logger.debug(f"Updated session data: {list(updates.keys())}")
            return True
    
    def add_vocabulary_practiced(self, word: str) -> None:
        """Add a word to the practiced vocabulary list."""
        if self.current_session and self.current_session.is_active:
            if word not in self.current_session.vocab_practiced:
                self.current_session.vocab_practiced.append(word)
                self._update_session_in_db(self.current_session)
    
    def add_new_vocabulary(self, word: str) -> None:
        """Add a new word to the learned vocabulary list."""
        if self.current_session and self.current_session.is_active:
            if word not in self.current_session.new_vocab_learned:
                self.current_session.new_vocab_learned.append(word)
                self._update_session_in_db(self.current_session)
    
    def add_correction(self, correction: Dict[str, Any]) -> None:
        """Add a correction to the session."""
        if self.current_session and self.current_session.is_active:
            self.current_session.corrections_made.append(correction)
            self._update_session_in_db(self.current_session)
    
    def update_engagement_score(self, score: float) -> None:
        """Update the session engagement score."""
        if self.current_session and self.current_session.is_active:
            self.current_session.engagement_score = max(0.0, min(1.0, score))
            self._update_session_in_db(self.current_session)
    
    def update_difficulty_level(self, level: float) -> None:
        """Update the session difficulty level."""
        if self.current_session and self.current_session.is_active:
            self.current_session.difficulty_level = max(0.1, min(5.0, level))
            self._update_session_in_db(self.current_session)
    
    def get_current_session(self) -> Optional[SessionState]:
        """Get the current session state."""
        return self.current_session
    
    def get_session_history(self, limit: int = 50) -> List[SessionState]:
        """Get recent session history."""
        with self._lock:
            return self.session_history[-limit:]
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionState]:
        """Get a specific session by ID."""
        # Check current session
        if self.current_session and self.current_session.session_id == session_id:
            return self.current_session
        
        # Check history
        for session in self.session_history:
            if session.session_id == session_id:
                return session
        
        # Check database
        return self._load_session_from_db(session_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self._lock:
            return {
                'total_sessions': self.total_sessions,
                'total_duration': self.total_duration,
                'average_engagement': self.average_engagement,
                'current_session_active': self.current_session is not None and self.current_session.is_active,
                'sessions_today': self._get_sessions_today(),
                'average_session_duration': self._get_average_session_duration(),
                'most_common_mode': self._get_most_common_mode()
            }
    
    def start_background_tasks(self) -> None:
        """Start background tasks."""
        self.is_running = True
        self.stop_background.clear()
        
        self.background_thread = threading.Thread(
            target=self._background_task_loop,
            daemon=True
        )
        self.background_thread.start()
        
        self.logger.info("Session manager background tasks started")
    
    def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        self.is_running = False
        self.stop_background.set()
        
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=5.0)
        
        self.logger.info("Session manager background tasks stopped")
    
    def _background_task_loop(self) -> None:
        """Background task loop."""
        while self.is_running and not self.stop_background.is_set():
            try:
                # Perform periodic tasks
                self._perform_periodic_tasks()
                
                # Sleep for a short interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in background task loop: {e}", exc_info=True)
                time.sleep(60)  # Wait longer on error
    
    def _perform_periodic_tasks(self) -> None:
        """Perform periodic maintenance tasks."""
        # Update current session duration if active
        if self.current_session and self.current_session.is_active:
            current_duration = int(
                (datetime.now() - self.current_session.started_at).total_seconds()
            )
            if current_duration != self.current_session.duration_seconds:
                self.current_session.duration_seconds = current_duration
                self._update_session_in_db(self.current_session)
        
        # Clean up old sessions from memory
        self._cleanup_old_sessions()
    
    def _save_session_to_db(self, session: SessionState) -> None:
        """Save session to database."""
        try:
            data = {
                'id': session.session_id,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'duration_seconds': session.duration_seconds,
                'mode': session.mode,
                'summary': session.notes,
                'vocab_practiced': session.vocab_practiced,
                'new_vocab_learned': session.new_vocab_learned,
                'corrections_made': session.corrections_made,
                'engagement_score': session.engagement_score,
                'difficulty_level': session.difficulty_level,
                'archived': False
            }
            
            self.db.insert('learning_sessions', data)
            
        except Exception as e:
            self.logger.error(f"Failed to save session to database: {e}", exc_info=True)
    
    def _update_session_in_db(self, session: SessionState) -> None:
        """Update session in database."""
        try:
            data = {
                'ended_at': session.ended_at,
                'duration_seconds': session.duration_seconds,
                'summary': session.notes,
                'vocab_practiced': session.vocab_practiced,
                'new_vocab_learned': session.new_vocab_learned,
                'corrections_made': session.corrections_made,
                'engagement_score': session.engagement_score,
                'difficulty_level': session.difficulty_level
            }
            
            self.db.update('learning_sessions', data, 'id = ?', (session.session_id,))
            
        except Exception as e:
            self.logger.error(f"Failed to update session in database: {e}", exc_info=True)
    
    def _load_session_from_db(self, session_id: str) -> Optional[SessionState]:
        """Load session from database."""
        try:
            result = self.db.fetch_dict(
                'SELECT * FROM learning_sessions WHERE id = ?',
                (session_id,)
            )
            
            if result:
                # Parse JSON fields safely - they may be stored as JSON strings
                def safe_parse_json_list(value):
                    if not value:
                        return []
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return []
                    elif isinstance(value, list):
                        return value
                    return []
                
                vocab_practiced = safe_parse_json_list(result['vocab_practiced'])
                new_vocab_learned = safe_parse_json_list(result['new_vocab_learned'])
                corrections_made = safe_parse_json_list(result['corrections_made'])
                
                # Parse datetime fields safely
                started_at = result['started_at']
                if isinstance(started_at, str):
                    started_at = datetime.fromisoformat(started_at)
                
                ended_at = result['ended_at']
                if ended_at and isinstance(ended_at, str):
                    ended_at = datetime.fromisoformat(ended_at)
                
                return SessionState(
                    session_id=result['id'],
                    started_at=started_at,
                    ended_at=ended_at,
                    duration_seconds=result['duration_seconds'] or 0,
                    mode=result['mode'],
                    is_active=False,
                    engagement_score=float(result['engagement_score']) if result['engagement_score'] else 0.0,
                    difficulty_level=float(result['difficulty_level']) if result['difficulty_level'] else 1.0,
                    vocab_practiced=vocab_practiced,
                    new_vocab_learned=new_vocab_learned,
                    corrections_made=corrections_made,
                    notes=result['summary'] or ""
                )
            
        except Exception as e:
            self.logger.error(f"Failed to load session from database: {e}", exc_info=True)
        
        return None
    
    def _update_statistics(self) -> None:
        """Update session statistics."""
        if not self.current_session:
            return
        
        self.total_sessions += 1
        self.total_duration += self.current_session.duration_seconds
        
        # Calculate average engagement
        if self.total_sessions > 0:
            total_engagement = sum(
                s.engagement_score for s in self.session_history
            ) + self.current_session.engagement_score
            self.average_engagement = total_engagement / (self.total_sessions + 1)
    
    def _cleanup_old_sessions(self) -> None:
        """Clean up old sessions from memory."""
        # Keep only last 100 sessions in memory
        if len(self.session_history) > 100:
            self.session_history = self.session_history[-100:]
    
    def _get_sessions_today(self) -> int:
        """Get number of sessions today."""
        today = datetime.now().date()
        count = 0
        
        # Count from current session
        if self.current_session and self.current_session.started_at.date() == today:
            count += 1
        
        # Count from history
        for session in self.session_history:
            if session.started_at.date() == today:
                count += 1
        
        return count
    
    def _get_average_session_duration(self) -> float:
        """Get average session duration."""
        if not self.session_history:
            return 0.0
        
        total_duration = sum(s.duration_seconds for s in self.session_history)
        return total_duration / len(self.session_history)
    
    def _get_most_common_mode(self) -> str:
        """Get most common session mode."""
        if not self.session_history:
            return "conversation"
        
        mode_counts = {}
        for session in self.session_history:
            mode_counts[session.mode] = mode_counts.get(session.mode, 0) + 1
        
        return max(mode_counts.items(), key=lambda x: x[1])[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        return self.get_statistics()


