# Real-time Voice Translator

A Python GUI application that provides real-time voice translation during calls. Perfect for understanding Thai, Indonesian, or any other language in real-time.

## Features

- 🎤 **Real-time Audio Capture**: Continuously monitors audio input
- 🌍 **Multi-language Translation**: Supports translation from any language to English (or other target languages)
- 🤖 **OpenAI Integration**: Uses GPT-4o-audio-preview for accurate translation
- 📱 **Modern GUI**: Clean, dark-themed interface
- ⚡ **Live Updates**: Translations appear instantly with timestamps
- 🔊 **Audio Level Monitoring**: Visual feedback of audio input levels
- 📌 **Always on Top**: Window stays visible during calls

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install PyAudio (Windows)

For Windows, you might need to install PyAudio separately:

```bash
pip install pipwin
pipwin install pyaudio
```

Or download the appropriate wheel file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### 3. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key for use in the application

## Usage

### 1. Run the Application

```bash
python realtime_voice_translator.py
```

### 2. Configure Settings

1. Enter your OpenAI API key in the configuration section
2. Select your target language (default: English)
3. Click "💾 Save Settings"

### 3. Start Translation

1. Click "🎤 Start Translation"
2. The application will start monitoring your microphone
3. Speak or have others speak in Thai, Indonesian, or any language
4. Translations will appear in real-time in the text area

### 4. During Calls

- Keep the application window open and visible
- The "Always on Top" feature ensures it stays visible
- Audio level bar shows current input levels
- Translations appear with timestamps

## Configuration

The application creates a `translator_config.json` file with these settings:

- `openai_api_key`: Your OpenAI API key
- `source_language`: Source language detection (auto-detect)
- `target_language`: Target language for translation
- `audio_threshold`: Minimum audio level to process (reduces noise)
- `translation_model`: OpenAI model to use

## Troubleshooting

### Audio Issues

1. **No audio detected**: Check microphone permissions and ensure your microphone is working
2. **Poor quality**: Adjust the `audio_threshold` in config file
3. **Latency**: The app processes audio every 3 seconds for better accuracy

### API Issues

1. **Invalid API key**: Verify your OpenAI API key is correct
2. **Rate limits**: OpenAI has usage limits - check your account
3. **Model access**: Ensure you have access to GPT-4o-audio-preview

### Performance

- The app keeps only the last 50 translations to prevent memory issues
- Audio processing runs in background threads for smooth performance
- GUI updates are optimized for real-time display

## Tips for Best Results

1. **Clear Audio**: Ensure good microphone quality and minimal background noise
2. **Stable Internet**: Translation requires internet connection to OpenAI
3. **Proper Positioning**: Keep the app window visible but not blocking your call interface
4. **Language Detection**: The app auto-detects source language, works best with clear speech

## Supported Languages

The app can translate FROM any language TO:
- English (default)
- Spanish
- French
- German
- Chinese
- Japanese

You can modify the target language list in the code to add more languages.

## Cost Considerations

- Uses OpenAI's GPT-4o-audio-preview model
- Processes audio every 3 seconds when speech is detected
- Check OpenAI pricing for audio processing costs
- Consider adjusting `audio_threshold` to reduce unnecessary API calls