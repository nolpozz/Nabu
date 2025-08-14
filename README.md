# 🎤 AI Voice Assistant - Desktop

A native desktop voice conversation app built with Tkinter, PyAudio, OpenAI Whisper, GPT-4o-mini, and ElevenLabs TTS.

## Features

- 🎤 **Direct microphone access** via PyAudio (no browser needed)
- 🗣️ **Live transcription** using OpenAI Whisper API
- 🤖 **AI responses** from GPT-4o-mini
- 🔊 **Automatic audio playback** using system default player
- ⚡ **Low latency** processing with 3-second audio chunks
- 🖥️ **Native desktop GUI** - clean and responsive

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root with your API keys:

```bash
# .env file
OPENAI_API_KEY=your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
```

**Get API Keys:**
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [ElevenLabs API Key](https://elevenlabs.io/speech-synthesis)

### 3. Run the App

```bash
python desktop_app.py
```

### 4. Use the App

1. Click **"Start Recording"** to begin
2. Speak clearly for 3 seconds
3. Wait for AI response and transcription
4. Audio plays automatically
5. Repeat as needed

## How It Works

1. **Audio Capture**: PyAudio captures microphone audio directly
2. **Processing**: Audio is processed in 3-second chunks
3. **Transcription**: Whisper API converts speech to text
4. **AI Response**: GPT-4o-mini generates conversational responses
5. **TTS**: ElevenLabs converts AI responses to speech
6. **Playback**: Audio plays using system default player

## Technical Details

- **Native Audio**: Direct microphone access via PyAudio
- **Threading**: Background processing prevents GUI freezing
- **Error Handling**: Robust error handling for all components
- **Cross-platform**: Works on Windows, macOS, and Linux

## Troubleshooting

### PyAudio Installation Issues

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Common Issues

1. **Microphone not working**: Check system microphone permissions
2. **API errors**: Verify your API keys are correct and have sufficient credits
3. **Audio playback issues**: Ensure system has a default audio player
4. **No speech detected**: Speak clearly and ensure microphone is working

## Requirements

- Python 3.8+
- Microphone access
- OpenAI API key with Whisper access
- ElevenLabs API key
- Stable internet connection

## Advantages Over Web Version

- ✅ **No browser dependencies**
- ✅ **No WebRTC issues**
- ✅ **Reliable audio playback**
- ✅ **No threading warnings**
- ✅ **Better performance**
- ✅ **Native desktop experience**

## License

MIT License - feel free to modify and distribute!
