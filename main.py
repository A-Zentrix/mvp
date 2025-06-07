from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
from dpmodel import face
import json
import asyncio
import base64
import logging
import time
from typing import List, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Request Models
class MessageRequest(BaseModel):
    message: str
    session_id: str = "default"

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

# In-memory conversation storage
conversations: Dict[str, List[Message]] = {}

def get_conversation(session_id: str) -> List[Message]:
    if session_id not in conversations:
        conversations[session_id] = []
    return conversations[session_id]

def add_message(session_id: str, role: str, content: str):
    conversation = get_conversation(session_id)
    message = Message(
        role=role,
        content=content,
        timestamp=datetime.now().isoformat()
    )
    conversation.append(message)
    return message

# Initialize speech engine
try:
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty("rate", 170)
except Exception as e:
    logger.error(f"Failed to initialize speech engine: {e}")
    engine = None

# Configure Gemini AI
genai.configure(api_key="AIzaSyA_LfnvKFq5dLFKYpArkIXwjxqgiZaFD1s")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

def speak(audio):
    if engine is None:
        logger.warning("Speech engine not initialized")
        return
    try:
        engine.say(audio)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"Speech error: {e}")
        try:
            engine.endLoop()
            engine.say(audio)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"Failed to recover from speech error: {e}")

def bot(prompt, session_id: str = "default"):
    try:
        # Get conversation history
        conversation = get_conversation(session_id)
        
        # Create context from conversation history
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation[-5:]])  # Last 5 messages
        
        response = model.generate_content([
            "You are a compassionate and highly intelligent mental wellness assistant. Your role is to provide emotional support, help users manage stress, and guide them toward positive mental health. Speak in a warm, understanding, and friendly tone. Always prioritize empathy and avoid judgment.When interacting:Listen carefully to users' concerns and acknowledge their feelings.Offer actionable advice when necessary but only if the user seeks it.Share motivational and uplifting words during difficult times.Be conversational and supportive during good times, like a trusted friend.Encourage healthy coping mechanisms and, if needed, suggest seeking professional help but u need to speak whitin 20 to 30 words, don't use symbols,don't split ur replay into pras just end it one pra .",
            f"Previous conversation:\n{context}\n",
            f"User: {prompt}",
            "Assistant: ",
        ])
        return response.text
    except Exception as e:
        logger.error(f"Error in bot response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/detect-emotion")
async def detect_emotion():
    try:
        emotion = face()
        if emotion is None:
            return {"error": "No face detected. Please make sure your face is visible to the camera."}
        response = bot(f"I am feeling {emotion}")
        speak(response)
        return {"emotion": emotion, "response": response}
    except Exception as e:
        logger.error(f"Error in emotion detection: {e}")
        return {"error": "Failed to detect emotion. Please try again."}

@app.post("/send-message")
async def send_message(request: MessageRequest):
    try:
        # Add user message to conversation
        add_message(request.session_id, "user", request.message)
        
        # Get bot response
        response = bot(request.message, request.session_id)
        
        # Add bot response to conversation
        add_message(request.session_id, "assistant", response)
        
        speak(response)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in message processing: {e}")
        return {"error": "Failed to process message. Please try again."}

@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    try:
        conversation = get_conversation(session_id)
        return {"messages": [msg.dict() for msg in conversation]}
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return {"error": "Failed to get conversation history."}

def test_microphone(mic):
    """Test if the microphone is working properly."""
    if mic is None:
        return False
        
    try:
        recognizer = sr.Recognizer()
        with mic as source:
            logger.info("Testing microphone...")
            try:
                # Quick test to see if we can get audio
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                return True
            except sr.WaitTimeoutError:
                logger.warning("Microphone test failed - no audio detected")
                return False
            except Exception as e:
                logger.error(f"Microphone test error: {e}")
                return False
    except Exception as e:
        logger.error(f"Microphone test error: {e}")
        return False

def get_microphone():
    """Get the best available microphone."""
    try:
        # List all microphones
        mics = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {mics}")
        
        # Try to find Realtek HD Audio Mic first
        realtek_mic_index = None
        for i, mic in enumerate(mics):
            if "Realtek" in mic and "Mic" in mic:
                realtek_mic_index = i
                break
        
        if realtek_mic_index is not None:
            logger.info(f"Found Realtek HD Audio Mic at index {realtek_mic_index}")
            try:
                mic = sr.Microphone(device_index=realtek_mic_index)
                if test_microphone(mic):
                    logger.info("Realtek microphone test successful")
                    return mic
                else:
                    logger.warning("Realtek microphone test failed, trying Intel mic")
            except Exception as e:
                logger.error(f"Error initializing Realtek microphone: {e}")
        
        # Try Intel Smart Sound Technology microphone as fallback
        intel_mic_index = None
        for i, mic in enumerate(mics):
            if "Intel" in mic and "Smart" in mic and "Microphone" in mic:
                intel_mic_index = i
                break
        
        if intel_mic_index is not None:
            logger.info(f"Using Intel Smart Sound Technology microphone at index {intel_mic_index}")
            try:
                mic = sr.Microphone(device_index=intel_mic_index)
                if test_microphone(mic):
                    logger.info("Intel microphone test successful")
                    return mic
                else:
                    logger.warning("Intel microphone test failed")
            except Exception as e:
                logger.error(f"Error initializing Intel microphone: {e}")
        
        # Try Primary Sound Capture Driver as fallback
        primary_mic_index = None
        for i, mic in enumerate(mics):
            if "Primary Sound Capture Driver" in mic:
                primary_mic_index = i
                break
        
        if primary_mic_index is not None:
            logger.info(f"Using Primary Sound Capture Driver at index {primary_mic_index}")
            try:
                mic = sr.Microphone(device_index=primary_mic_index)
                if test_microphone(mic):
                    logger.info("Primary microphone test successful")
                    return mic
                else:
                    logger.warning("Primary microphone test failed")
            except Exception as e:
                logger.error(f"Error initializing Primary microphone: {e}")
        
        # Last resort: try default microphone
        logger.info("Using default microphone")
        try:
            mic = sr.Microphone()
            if test_microphone(mic):
                logger.info("Default microphone test successful")
                return mic
            else:
                logger.warning("Default microphone test failed")
        except Exception as e:
            logger.error(f"Error initializing default microphone: {e}")
        
        raise Exception("No working microphone found")
        
    except Exception as e:
        logger.error(f"Error getting microphone: {e}")
        return None

@app.post("/voice-recognition")
async def voice_recognition():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Listening...")
            audio = r.listen(source, timeout=4, phrase_time_limit=4)
            
            logger.info("Recognizing...")
            try:
                text = r.recognize_google(audio, language='en-in')
                if not text.strip():
                    return {"error": "No speech detected. Please try speaking again."}
                
                logger.info(f"Recognized text: {text}")
                return {"text": text}
                
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return {"error": "Could not understand audio. Please speak clearly and try again."}
                
            except sr.RequestError as e:
                logger.error(f"Could not request results from speech recognition service: {e}")
                return {"error": "Speech recognition service is currently unavailable. Please try again later."}
                
    except sr.WaitTimeoutError:
        logger.warning("No speech detected within timeout")
        return {"error": "No speech detected. Please speak louder or check your microphone."}
        
    except Exception as e:
        logger.error(f"Error in voice recognition: {e}")
        return {"error": "An error occurred during voice recognition. Please try again."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            response = bot(data)
            await websocket.send_text(response)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass 