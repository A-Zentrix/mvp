# AI Mental Wellness Assistant

A modern web application that provides mental wellness support using AI, featuring emotion detection, voice commands, and real-time chat.

## Features

- 🤖 AI-powered mental wellness support
- 😊 Emotion detection
- 🎤 Voice command support
- 💬 Real-time chat interface
- 🌈 Modern, responsive UI
- 🔄 WebSocket support for real-time communication

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the necessary Python packages for speech recognition and text-to-speech:
- For Windows: `pip install pywin32`
- For Linux: `sudo apt-get install python3-espeak`
- For macOS: `brew install espeak`

3. Run the application:
```bash
uvicorn main:app --reload
```

4. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

- Type your message in the input field and press Enter or click Send
- Click the "Detect Emotion" button to analyze your current emotional state
- Use the "Voice Command" button to speak your message
- The AI will respond with supportive and helpful messages

## Technologies Used

- FastAPI
- WebSocket
- Google Gemini AI
- Speech Recognition
- Text-to-Speech
- Modern HTML5/CSS3
- JavaScript (ES6+)

## Note

Make sure you have a working microphone for voice commands and emotion detection features. 