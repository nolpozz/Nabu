"""
Event bus system for the AI Language Tutor application.
Handles inter-component communication through a publish-subscribe pattern.
"""

import threading
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from datetime import datetime
import json

from utils.logger import get_logger, LoggerMixin


class EventBus(LoggerMixin):
    """Event bus for inter-component communication."""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._lock = threading.RLock()
        
        self.logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type."""
        with self._lock:
            self.subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Unsubscribe from an event type."""
        with self._lock:
            if event_type in self.subscribers:
                try:
                    self.subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from event: {event_type}")
                    return True
                except ValueError:
                    self.logger.warning(f"Callback not found for event: {event_type}")
                    return False
            return False
    
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'thread_id': threading.get_ident()
        }
        
        # Store in history
        with self._lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
        
        # Get subscribers for this event type
        with self._lock:
            callbacks = self.subscribers[event_type].copy()
        
        # Call all subscribers
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(
                    f"Error in event callback for {event_type}: {e}",
                    exc_info=True
                )
        
        self.logger.debug(f"Published event: {event_type} with {len(callbacks)} subscribers")
    
    def publish_async(self, event_type: str, data: Any = None) -> None:
        """Publish an event asynchronously."""
        def async_publish():
            self.publish(event_type, data)
        
        thread = threading.Thread(target=async_publish, daemon=True)
        thread.start()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type."""
        with self._lock:
            return len(self.subscribers.get(event_type, []))
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered by event type."""
        with self._lock:
            if event_type:
                filtered_history = [
                    event for event in self.event_history 
                    if event['type'] == event_type
                ]
                return filtered_history[-limit:]
            else:
                return self.event_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self.event_history.clear()
            self.logger.info("Event history cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            stats = {
                'total_events': len(self.event_history),
                'subscriber_counts': {
                    event_type: len(callbacks)
                    for event_type, callbacks in self.subscribers.items()
                },
                'total_subscribers': sum(len(callbacks) for callbacks in self.subscribers.values()),
                'event_types': list(self.subscribers.keys())
            }
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown the event bus."""
        with self._lock:
            self.subscribers.clear()
            self.event_history.clear()
        
        self.logger.info("EventBus shutdown completed")


# Global event bus instance
event_bus = EventBus()


# Event type constants
class EventTypes:
    """Constants for common event types."""
    
    # Navigation events
    NAVIGATE_TO_DASHBOARD = "navigate_to_dashboard"
    NAVIGATE_TO_CONVERSATION = "navigate_to_conversation"
    NAVIGATE_TO_SETTINGS = "navigate_to_settings"
    NAVIGATE_TO_HOME = "navigate_to_home"
    NAVIGATE_TO_VOCAB = "navigate_to_vocab"
    NAVIGATE_TO_MEDIA = "navigate_to_media"
    NAVIGATE_TO_GRAMMAR = "navigate_to_grammar"
    NAVIGATE_TO_NOTES = "navigate_to_notes"
    NAVIGATE_TO_TAB = "navigate_to_tab"
    
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    
    # Audio events
    AUDIO_STARTED = "audio_started"
    AUDIO_STOPPED = "audio_stopped"
    AUDIO_ERROR = "audio_error"
    SPEECH_DETECTED = "speech_detected"
    SILENCE_DETECTED = "silence_detected"
    
    # Message events
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    
    # TTS events
    TTS_COMPLETED = "tts_completed"
    TTS_ERROR = "tts_error"
    
    # Agent events
    AGENT_RESPONSE_READY = "agent_response_ready"
    AGENT_ERROR = "agent_error"
    AGENT_THINKING = "agent_thinking"
    
    # UI events
    UPDATE_DASHBOARD = "update_dashboard"
    UPDATE_CONVERSATION = "update_conversation"
    SHOW_NOTIFICATION = "show_notification"
    HIDE_NOTIFICATION = "hide_notification"
    
    # Learning events
    VOCABULARY_LEARNED = "vocabulary_learned"
    VOCABULARY_REVIEWED = "vocabulary_reviewed"
    QUIZ_COMPLETED = "quiz_completed"
    PROGRESS_UPDATED = "progress_updated"
    LANGUAGE_CHANGED = "language_changed"
    
    # System events
    APPLICATION_STARTED = "application_started"
    APPLICATION_CLOSING = "application_closing"
    APPLICATION_SHUTDOWN = "application_shutdown"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"


# Convenience functions for common events
def publish_navigation(target: str) -> None:
    """Publish a navigation event."""
    if target == "dashboard":
        event_bus.publish(EventTypes.NAVIGATE_TO_DASHBOARD)
    elif target == "conversation":
        event_bus.publish(EventTypes.NAVIGATE_TO_CONVERSATION)
    elif target == "settings":
        event_bus.publish(EventTypes.NAVIGATE_TO_SETTINGS)


def publish_session_event(event_type: str, session_data: Dict[str, Any]) -> None:
    """Publish a session-related event."""
    event_bus.publish(event_type, session_data)


def publish_audio_event(event_type: str, audio_data: Dict[str, Any]) -> None:
    """Publish an audio-related event."""
    event_bus.publish(event_type, audio_data)


def publish_agent_event(event_type: str, agent_data: Dict[str, Any]) -> None:
    """Publish an agent-related event."""
    event_bus.publish(event_type, agent_data)


def publish_ui_update(component: str, data: Dict[str, Any]) -> None:
    """Publish a UI update event."""
    if component == "dashboard":
        event_bus.publish(EventTypes.UPDATE_DASHBOARD, data)
    elif component == "conversation":
        event_bus.publish(EventTypes.UPDATE_CONVERSATION, data)


def publish_notification(message: str, notification_type: str = "info", duration: int = 5000) -> None:
    """Publish a notification event."""
    notification_data = {
        'message': message,
        'type': notification_type,
        'duration': duration
    }
    event_bus.publish(EventTypes.SHOW_NOTIFICATION, notification_data)


def publish_error(error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
    """Publish an error event."""
    error_data = {
        'message': error_message,
        'details': error_details or {},
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish(EventTypes.ERROR_OCCURRED, error_data)
