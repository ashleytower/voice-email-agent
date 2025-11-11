"""
FastAPI/Websocket Server - Voice-First AI Email Agent

This module implements the API entry point with streaming speech-to-speech support.
"""
import os
import json
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from .config import settings
from .workflow import process_user_input


# Initialize Sentry if DSN is provided
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        environment=settings.environment,
        traces_sample_rate=1.0 if settings.environment == "development" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("🚀 Voice-First AI Email Agent starting up...")
    print(f"Environment: {settings.environment}")
    yield
    # Shutdown
    print("👋 Voice-First AI Email Agent shutting down...")


app = FastAPI(
    title="Voice-First AI Email Agent",
    description="A robust, production-ready AI email agent with voice-first interaction",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Voice-First AI Email Agent",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "services": {
            "openai": bool(settings.openai_api_key),
            "supabase": bool(settings.supabase_url),
            "gmail": bool(settings.gmail_client_id),
            "google_cloud": bool(settings.google_cloud_project)
        }
    }


async def transcribe_audio_stream(audio_data: bytes) -> str:
    """
    Transcribe audio data to text using the voice CLI tool.
    
    Args:
        audio_data: Raw audio bytes
    
    Returns:
        Transcribed text
    """
    # Save audio to temporary file
    temp_audio_path = "/tmp/user_audio.wav"
    with open(temp_audio_path, "wb") as f:
        f.write(audio_data)
    
    # Call voice CLI tool
    result = subprocess.run(
        ["python", "tools/voice_cli.py", "transcribe", "--file", temp_audio_path],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/voice-email-agent"
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data.get("text", "")
    else:
        raise Exception(f"Transcription failed: {result.stderr}")


async def synthesize_speech_stream(text: str) -> bytes:
    """
    Convert text to speech using the voice CLI tool.
    
    Args:
        text: Text to convert to speech
    
    Returns:
        Audio data as bytes
    """
    temp_output_path = "/tmp/agent_response.mp3"
    
    # Call voice CLI tool
    result = subprocess.run(
        ["python", "tools/voice_cli.py", "speak", "--text", text, "--output", temp_output_path],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/voice-email-agent"
    )
    
    if result.returncode == 0:
        with open(temp_output_path, "rb") as f:
            return f.read()
    else:
        raise Exception(f"Speech synthesis failed: {result.stderr}")


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming speech-to-speech interaction.
    
    Protocol:
    1. Client sends audio data (binary)
    2. Server transcribes audio to text
    3. Server processes text through LangGraph workflow
    4. Server converts response text to speech
    5. Server sends audio response back to client
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive audio data from client
            audio_data = await websocket.receive_bytes()
            
            # Send acknowledgment
            await websocket.send_json({"status": "processing", "message": "Transcribing audio..."})
            
            try:
                # Step 1: Transcribe audio to text
                user_text = await transcribe_audio_stream(audio_data)
                
                if not user_text:
                    await websocket.send_json({"status": "error", "message": "Could not transcribe audio"})
                    continue
                
                await websocket.send_json({
                    "status": "processing",
                    "message": "Processing request...",
                    "transcription": user_text
                })
                
                # Step 2: Process through LangGraph workflow
                response_text = await asyncio.to_thread(process_user_input, user_text)
                
                await websocket.send_json({
                    "status": "processing",
                    "message": "Generating speech...",
                    "response_text": response_text
                })
                
                # Step 3: Convert response to speech
                response_audio = await synthesize_speech_stream(response_text)
                
                # Step 4: Send audio response to client
                await websocket.send_json({
                    "status": "complete",
                    "message": "Response ready",
                    "audio_size": len(response_audio)
                })
                
                await websocket.send_bytes(response_audio)
                
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Processing error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        print("Client disconnected from voice websocket")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "status": "error",
                "message": f"Server error: {str(e)}"
            })
        except:
            pass


@app.post("/api/text")
async def text_endpoint(request: dict):
    """
    REST endpoint for text-based interaction (non-voice).
    
    Request body:
        {
            "text": "User's text input"
        }
    
    Response:
        {
            "response": "Agent's text response"
        }
    """
    user_text = request.get("text", "")
    
    if not user_text:
        return {"error": "No text provided"}
    
    try:
        response_text = await asyncio.to_thread(process_user_input, user_text)
        return {"response": response_text}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
