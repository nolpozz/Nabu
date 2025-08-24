"""
Configuration management for the AI Language Tutor application.
Handles environment variables, default settings, and dynamic configuration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AudioConfig:
    """Audio system configuration."""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    silence_threshold: float = 3.0  # Further increased to reduce false triggers
    min_speech_duration: float = 1.2  # Increased to require longer speech
    rms_threshold: int = 35  # Increased to require louder audio
    zcr_threshold: float = 0.003  # Increased to reduce noise triggers
    debug_audio: bool = True


@dataclass
class UIConfig:
    """UI system configuration."""
    window_width: int = 1400
    window_height: int = 900
    theme: str = "dark"
    font_family: str = "SF Pro Display"
    font_size_base: int = 15
    animation_speed: float = 0.3
    enable_sounds: bool = True


@dataclass
class AgentConfig:
    """AI agent configuration."""
    model: str = "gpt-4o-mini"
    max_tokens: int = 150
    temperature: float = 0.7
    system_prompt_template: str = "default"
    enable_tools: bool = True
    max_conversation_history: int = 10
    response_timeout: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "data/tutor.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backup_count: int = 7
    retention_days: int = 365


@dataclass
class LearningConfig:
    """Learning system configuration."""
    srs_enabled: bool = True
    vocab_review_interval_hours: int = 24
    max_active_vocab: int = 750
    difficulty_adjustment_rate: float = 0.1
    engagement_threshold: float = 0.7
    session_timeout_minutes: int = 30
    target_language: str = "en"  # Language being practiced (ISO 639-1 code)
    native_language: str = "en"  # User's native language (ISO 639-1 code)
    test_mode: bool = False  # Test mode - conversations not logged to database


@dataclass
class SecurityConfig:
    """Security configuration."""
    encrypt_user_data: bool = True
    encryption_key_path: str = "config/encryption.key"
    api_key_rotation_days: int = 90
    session_timeout_minutes: int = 60


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    max_concurrent_requests: int = 5
    cache_enabled: bool = True
    cache_size_mb: int = 100
    log_level: str = "INFO"
    enable_profiling: bool = False


class Config:
    """Main configuration class that manages all application settings."""
    
    def __init__(self):
        self.audio = AudioConfig()
        self.ui = UIConfig()
        self.agent = AgentConfig()
        self.database = DatabaseConfig()
        self.learning = LearningConfig()
        self.security = SecurityConfig()
        self.performance = PerformanceConfig()
        
        # API Keys
        self.openai_api_key: Optional[str] = None
        self.elevenlabs_api_key: Optional[str] = None
        
        # Application paths
        self.app_dir = Path(__file__).parent
        self.data_dir = self.app_dir / "data"
        self.config_dir = self.app_dir / "config"
        self.assets_dir = self.app_dir / "assets"
        self.logs_dir = self.app_dir / "logs"
        
        # Load configuration
        self._load_environment_variables()
        self._create_directories()
        self._load_user_settings()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        # API Keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Validate required API keys
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        
        # Audio configuration
        if os.getenv('AUDIO_SAMPLE_RATE'):
            self.audio.sample_rate = int(os.getenv('AUDIO_SAMPLE_RATE'))
        if os.getenv('AUDIO_SILENCE_THRESHOLD'):
            self.audio.silence_threshold = float(os.getenv('AUDIO_SILENCE_THRESHOLD'))
        if os.getenv('AUDIO_DEBUG'):
            self.audio.debug_audio = os.getenv('AUDIO_DEBUG').lower() == 'true'
        
        # UI configuration
        if os.getenv('UI_THEME'):
            self.ui.theme = os.getenv('UI_THEME')
        if os.getenv('UI_WINDOW_WIDTH'):
            self.ui.window_width = int(os.getenv('UI_WINDOW_WIDTH'))
        if os.getenv('UI_WINDOW_HEIGHT'):
            self.ui.window_height = int(os.getenv('UI_WINDOW_HEIGHT'))
        
        # Agent configuration
        if os.getenv('AGENT_MODEL'):
            self.agent.model = os.getenv('AGENT_MODEL')
        if os.getenv('AGENT_MAX_TOKENS'):
            self.agent.max_tokens = int(os.getenv('AGENT_MAX_TOKENS'))
        if os.getenv('AGENT_TEMPERATURE'):
            self.agent.temperature = float(os.getenv('AGENT_TEMPERATURE'))
        
        # Database configuration
        if os.getenv('DB_PATH'):
            self.database.db_path = os.getenv('DB_PATH')
        if os.getenv('DB_BACKUP_ENABLED'):
            self.database.backup_enabled = os.getenv('DB_BACKUP_ENABLED').lower() == 'true'
        
        # Learning configuration
        if os.getenv('LEARNING_SRS_ENABLED'):
            self.learning.srs_enabled = os.getenv('LEARNING_SRS_ENABLED').lower() == 'true'
        if os.getenv('LEARNING_MAX_VOCAB'):
            self.learning.max_active_vocab = int(os.getenv('LEARNING_MAX_VOCAB'))
        
        # Performance configuration
        if os.getenv('LOG_LEVEL'):
            self.performance.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('ENABLE_PROFILING'):
            self.performance.enable_profiling = os.getenv('ENABLE_PROFILING').lower() == 'true'
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.config_dir,
            self.assets_dir,
            self.logs_dir,
            self.assets_dir / "icons",
            self.assets_dir / "fonts",
            self.assets_dir / "sounds",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_user_settings(self):
        """Load user-specific settings from file."""
        settings_file = self.config_dir / "user_settings.json"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Apply user settings
                if 'audio' in settings:
                    for key, value in settings['audio'].items():
                        if hasattr(self.audio, key):
                            setattr(self.audio, key, value)
                
                if 'ui' in settings:
                    for key, value in settings['ui'].items():
                        if hasattr(self.ui, key):
                            setattr(self.ui, key, value)
                
                if 'agent' in settings:
                    for key, value in settings['agent'].items():
                        if hasattr(self.agent, key):
                            setattr(self.agent, key, value)
                
                if 'learning' in settings:
                    for key, value in settings['learning'].items():
                        if hasattr(self.learning, key):
                            setattr(self.learning, key, value)
                            
            except Exception as e:
                print(f"Warning: Could not load user settings: {e}")
    
    def save_user_settings(self):
        """Save current configuration as user settings."""
        settings_file = self.config_dir / "user_settings.json"
        
        settings = {
            'audio': {
                'sample_rate': self.audio.sample_rate,
                'silence_threshold': self.audio.silence_threshold,
                'debug_audio': self.audio.debug_audio,
            },
            'ui': {
                'theme': self.ui.theme,
                'window_width': self.ui.window_width,
                'window_height': self.ui.window_height,
                'font_family': self.ui.font_family,
                'font_size_base': self.ui.font_size_base,
            },
            'agent': {
                'model': self.agent.model,
                'max_tokens': self.agent.max_tokens,
                'temperature': self.agent.temperature,
            },
            'learning': {
                'srs_enabled': self.learning.srs_enabled,
                'max_active_vocab': self.learning.max_active_vocab,
                'difficulty_adjustment_rate': self.learning.difficulty_adjustment_rate,
                'target_language': self.learning.target_language,
                'native_language': self.learning.native_language,
            }
        }
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user settings: {e}")
    
    def get_database_path(self) -> Path:
        """Get the full database path."""
        return self.app_dir / self.database.db_path
    
    def get_log_path(self) -> Path:
        """Get the log file path."""
        return self.logs_dir / "tutor.log"
    
    def set_target_language(self, language_code: str) -> None:
        """Set the target language for learning."""
        self.learning.target_language = language_code
        self.save_user_settings()
    
    def set_native_language(self, language_code: str) -> None:
        """Set the user's native language."""
        self.learning.native_language = language_code
        self.save_user_settings()
    
    def validate(self) -> bool:
        """Validate the configuration."""
        errors = []
        
        # Check API keys
        if not self.openai_api_key:
            errors.append("OpenAI API key is required")
        if not self.elevenlabs_api_key:
            errors.append("ElevenLabs API key is required")
        
        # Check audio settings
        if self.audio.sample_rate <= 0:
            errors.append("Audio sample rate must be positive")
        if self.audio.silence_threshold <= 0:
            errors.append("Silence threshold must be positive")
        
        # Check UI settings
        if self.ui.window_width <= 0 or self.ui.window_height <= 0:
            errors.append("Window dimensions must be positive")
        
        # Check agent settings
        if self.agent.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        if not 0 <= self.agent.temperature <= 2:
            errors.append("Temperature must be between 0 and 2")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'audio': self.audio.__dict__,
            'ui': self.ui.__dict__,
            'agent': self.agent.__dict__,
            'database': self.database.__dict__,
            'learning': self.learning.__dict__,
            'security': self.security.__dict__,
            'performance': self.performance.__dict__,
            'app_dir': str(self.app_dir),
            'data_dir': str(self.data_dir),
            'config_dir': str(self.config_dir),
            'assets_dir': str(self.assets_dir),
            'logs_dir': str(self.logs_dir),
        }


# Global configuration instance
config = Config()

# Validate configuration on import
try:
    config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    raise
