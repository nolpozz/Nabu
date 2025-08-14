#!/usr/bin/env python3
"""
Test script for Desktop AI Voice Assistant
This script tests if all dependencies are properly installed.
"""

import sys
import importlib

def test_imports():
    """Test if all required modules can be imported"""
    required_modules = [
        'tkinter',
        'pyaudio',
        'wave',
        'numpy',
        'openai',
        'requests',
        'tempfile',
        'os',
        'time',
        'threading',
        'queue',
        'dotenv'
    ]
    
    print("🔍 Testing imports...")
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Please install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

def test_audio_devices():
    """Test if audio devices are available"""
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        
        print("\n🎤 Testing audio devices...")
        input_devices = []
        
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append((i, device_info['name']))
                print(f"✅ Input Device {i}: {device_info['name']}")
        
        if input_devices:
            print(f"\n✅ Found {len(input_devices)} input device(s)")
            return True
        else:
            print("\n❌ No input devices found!")
            return False
            
    except Exception as e:
        print(f"\n❌ Audio test failed: {e}")
        return False
    finally:
        try:
            audio.terminate()
        except:
            pass

def test_api_keys():
    """Test if API keys are set"""
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        print("\n🔑 Testing API keys...")
        
        openai_key = os.getenv('OPENAI_API_KEY')
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not openai_key:
            print("❌ OpenAI API key not found in .env file")
            return False
        else:
            print("✅ OpenAI API key found")
            
        if not elevenlabs_key:
            print("❌ ElevenLabs API key not found in .env file")
            return False
        else:
            print("✅ ElevenLabs API key found")
            
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

def main():
    print("🧪 Desktop AI Voice Assistant - Dependency Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test audio devices
    audio_ok = test_audio_devices()
    
    # Test API keys
    api_ok = test_api_keys()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Audio: {'✅ PASS' if audio_ok else '❌ FAIL'}")
    print(f"API Keys: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if all([imports_ok, audio_ok, api_ok]):
        print("\n🎉 All tests passed! You can run the desktop app:")
        print("python desktop_app.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
    return all([imports_ok, audio_ok, api_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
