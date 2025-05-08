# 🔊 Vani – Your Intelligent Voice Assistant

**Vani** is an advanced voice-controlled AI assistant that combines speech recognition, natural language processing, and various APIs to provide a comprehensive virtual assistant experience. Built with Python, Vani can understand and respond to voice commands, manage music playback, provide information, and engage in natural conversations.

---

## 🎯 Key Features

- 🎤 **Voice Control**: Natural voice interaction using speech recognition
- 🎵 **Music Management**: Play, pause, resume, and control music from YouTube
- 🌍 **Multilingual Support**: Translation capabilities with native accent pronunciation
- 📚 **Information Access**: Wikipedia searches, weather updates, and time information
- 💬 **Natural Conversations**: Powered by Google's Gemini AI for engaging discussions
- 📝 **File Operations**: Read text files, PDFs, and screen text using OCR
- 🎮 **System Control**: Open applications and manage system functions
- 🧠 **Memory System**: Remember and recall information as requested

---

## 🔧 Technologies Used

- Python
- Speech Recognition (speech_recognition)
- Text-to-Speech (pyttsx3, gTTS)
- Google Gemini AI
- VLC Media Player
- YouTube-DL
- PyAutoGUI
- Tesseract OCR
- Google Translate API
- OpenWeather API
- Wikipedia API

---

## 🚀 Getting Started

1. **Prerequisites**
   - Python 3.x
   - VLC Media Player installed
   - Tesseract OCR installed (for screen text reading)
   - Google API key for Gemini AI
   - OpenWeather API key

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   Create a `config.py` file with your API keys:
   ```python
   GOOGLE_API_KEY = "your_google_api_key"
   OPENWEATHER_API_KEY = "your_openweather_api_key"
   ```

4. **Run Vani**
   ```bash
   python main.py
   ```

---

## 💡 Voice Commands

Vani responds to various voice commands including:

- "Play [song name]" - Play music from YouTube
- "Weather in [city]" - Get weather information
- "Time" - Get current time
- "Wikipedia [topic]" - Search Wikipedia
- "Open [application]" - Launch applications
- "Translate [text] to [language]" - Translate text
- "Read file [path]" - Read text/PDF files
- "Read screen" - Read text from screen
- "Remember that" - Store information
- "Do you remember" - Recall stored information
- "Tell me a joke" - Get a joke
- "Let's chat" - Start a conversation
- "Ask Gemini" - Query Gemini AI

---

## ✨ Name Inspiration

The name **Vani** comes from Hindu mythology, symbolizing **speech, wisdom, and knowledge**, inspired by Goddess Saraswati.

---

## 🤝 Contributing

Contributions, issues, and suggestions are welcome! Feel free to fork the project and submit a PR.

---

*Speak smart. Think Vani.*
