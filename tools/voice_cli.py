#!/usr/bin/env python3
"""
Voice CLI Tool - MCP-Optimized Speech Operations

This tool provides CLI commands for speech-to-text and text-to-speech operations
using Google Cloud APIs, following the Code Execution with MCP pattern.

Usage:
    python voice_cli.py transcribe --file "path/to/audio.wav"
    python voice_cli.py speak --text "Hello, how can I help you?" --output "response.mp3"
"""
import argparse
import json
import sys
import os
from typing import Dict, Any
from google.cloud import speech
from google.cloud import texttospeech


def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """Transcribe audio file to text using Google Cloud Speech-to-Text."""
    try:
        client = speech.SpeechClient()
        
        with open(file_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        
        response = client.recognize(config=config, audio=audio)
        
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        return {
            "status": "success",
            "text": transcript.strip(),
            "confidence": response.results[0].alternatives[0].confidence if response.results else 0.0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def synthesize_speech(text: str, output_file: str = None) -> Dict[str, Any]:
    """Convert text to speech using Google Cloud Text-to-Speech."""
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-J",  # High-quality neural voice
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        if not output_file:
            output_file = "output.mp3"
        
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        return {
            "status": "success",
            "audio_file": output_file,
            "size_bytes": len(response.audio_content)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Voice CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio to text")
    transcribe_parser.add_argument("--file", required=True, help="Path to audio file")
    
    # Speak command
    speak_parser = subparsers.add_parser("speak", help="Convert text to speech")
    speak_parser.add_argument("--text", required=True, help="Text to convert to speech")
    speak_parser.add_argument("--output", help="Output audio file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    result = {}
    if args.command == "transcribe":
        result = transcribe_audio(args.file)
    elif args.command == "speak":
        result = synthesize_speech(args.text, args.output)
    
    # Output result as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
