# Nabu AI Language Tutor

A sophisticated desktop AI language tutor application built with Python and Tkinter, featuring voice interaction, intelligent conversation, and personalized learning.

## 🚀 Features

- **Voice-First Interaction**: Real-time speech-to-text and text-to-speech
- **Intelligent Conversations**: Powered by OpenAI GPT-4o-mini with context awareness
- **Personalized Learning**: Adaptive difficulty and personalized curriculum
- **Modern Dark UI**: Beautiful, responsive interface inspired by modern design systems
- **Session Management**: Track learning progress and session history
- **Vocabulary Management**: Spaced repetition system for vocabulary retention
- **Local-First Architecture**: All data stored locally with optional cloud sync

## 🏗️ Architecture

The application follows a modular, enterprise-grade architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │◄──►│ Orchestration   │◄──►│   Data Layer    │
│                 │    │     Layer       │    │                 │
│ • Dashboard     │    │ • Agent Core    │    │ • SQLite DB     │
│ • Conversation  │    │ • LangChain     │    │ • User Profile  │
│ • Components    │    │ • Action Parser │    │ • Learning Data │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Audio Layer    │
                    │                 │
                    │ • Voice Loop    │
                    │ • STT/TTS       │
                    │ • Audio Utils   │
                    └─────────────────┘
```

## 📋 Requirements

- Python 3.8+
- Windows 10/11 (primary), macOS, or Linux
- Microphone and speakers
- OpenAI API key
- ElevenLabs API key

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd desktop_ai_tutor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required API Keys
OPENAI_API_KEY=your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_SILENCE_THRESHOLD=1.5
AUDIO_DEBUG=true

# UI Configuration
UI_THEME=dark
UI_WINDOW_WIDTH=1200
UI_WINDOW_HEIGHT=800

# Agent Configuration
AGENT_MODEL=gpt-4o-mini
AGENT_MAX_TOKENS=150
AGENT_TEMPERATURE=0.7

# Learning Configuration
LEARNING_SRS_ENABLED=true
LEARNING_MAX_VOCAB=750
```

### API Keys Setup

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **ElevenLabs API Key**: Get from [ElevenLabs](https://elevenlabs.io/)

## 🎯 Usage

### Getting Started

1. **Launch the application**: Run `python main.py`
2. **Dashboard**: View your learning statistics and progress
3. **Start Conversation**: Click "Start Conversation" to begin a session
4. **Voice Interaction**: Click "Start Recording" and speak naturally
5. **End Session**: Click "End Session" when finished

### Features

- **Dashboard**: Overview of learning progress and statistics
- **Conversation Mode**: Natural voice-based language learning
- **Session Management**: Automatic tracking of learning sessions
- **Vocabulary Tracking**: Automatic detection and tracking of new words
- **Progress Analytics**: Detailed learning analytics and insights

## 🏗️ Project Structure

```
desktop_ai_tutor/
├── main.py                          # Application entry point
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── README.md                        # This file
├── 
├── core/                            # Core application logic
│   ├── application.py               # Main app controller
│   ├── session_manager.py           # Session lifecycle management
│   └── event_bus.py                 # Internal event system
│
├── ui/                              # User interface components
│   ├── theme.py                     # Dark theme & styling system
│   ├── dashboard.py                 # Stats & metrics dashboard
│   ├── conversation.py              # Main conversation interface
│   └── components/                  # Reusable UI components
│
├── audio/                           # Audio processing
│   ├── voice_loop.py                # Core audio capture/playback
│   ├── stt_service.py               # Speech-to-text service
│   └── tts_service.py               # Text-to-speech service
│
├── agent/                           # AI agent components
│   ├── orchestrator.py              # Main agent orchestration
│   ├── langchain_config.py          # LangChain setup
│   └── tools/                       # Agent tools
│
├── data/                            # Data layer
│   ├── database.py                  # SQLite connection & queries
│   ├── models.py                    # Data models & schemas
│   ├── migrations.py                # Database schema management
│   └── analytics.py                 # Learning analytics
│
├── learning/                        # Learning algorithms
│   ├── srs_engine.py                # Spaced repetition system
│   ├── difficulty_adapter.py        # Dynamic difficulty adjustment
│   └── curriculum_builder.py        # Personalized curriculum
│
├── utils/                           # Utility modules
│   ├── logger.py                    # Centralized logging
│   ├── validators.py                # Input validation
│   └── performance.py               # Performance monitoring
│
└── assets/                          # Static assets
    ├── icons/                       # UI icons
    ├── fonts/                       # Custom fonts
    └── sounds/                      # UI sound effects
```

## 🔍 Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Management

```bash
# Run migrations
python -m data.migrations

# Create sample data
python -m data.migrations --sample-data
```

## 🐛 Troubleshooting

### Common Issues

1. **Audio not working**:
   - Check microphone permissions
   - Verify PyAudio installation
   - Test with system audio settings

2. **API errors**:
   - Verify API keys in `.env` file
   - Check internet connection
   - Ensure API quotas are not exceeded

3. **Database errors**:
   - Run database migrations: `python -m data.migrations`
   - Check file permissions for database directory

### Logs

Application logs are stored in:
- `logs/tutor.log` - General application logs
- `logs/errors.log` - Error logs
- `logs/tutor_structured.log` - Structured JSON logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini
- ElevenLabs for text-to-speech
- The Python and Tkinter communities
- All contributors and testers

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Built with ❤️ for language learners everywhere**
