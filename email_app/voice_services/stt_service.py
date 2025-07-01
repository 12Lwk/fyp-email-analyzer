import os
import logging
import json
import io
from google.cloud import speech
from google.oauth2 import service_account
from django.conf import settings

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Service for converting speech to text using Google Cloud Speech-to-Text"""
    
    def __init__(self):
        # Get credentials file path
        credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'VOICE_ENABLE',
            'demo_speech_to_text_account.json'
        )
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            logger.error(f"STT credentials file not found at: {credentials_path}")
            raise FileNotFoundError(f"STT credentials file not found at: {credentials_path}")
        
        # Load credentials
        try:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = speech.SpeechClient(credentials=self.credentials)
            logger.info("Speech-to-Text service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize STT client: {str(e)}")
            raise
    
    def speech_to_text(self, audio_content, language_code="en-US", enable_automatic_punctuation=True):
        """Convert speech to text
        
        Args:
            audio_content: Binary audio content
            language_code: Language code for transcription
            enable_automatic_punctuation: Whether to add punctuation
            
        Returns:
            Transcribed text
        """
        try:
            # Create speech recognition config
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=enable_automatic_punctuation,
                model="default"  # Use "phone_call" for lower quality audio or noisy environments
            )
            
            # Create recognition audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Perform speech recognition
            response = self.client.recognize(config=config, audio=audio)
            
            # Process results
            transcription = ""
            for result in response.results:
                transcription += result.alternatives[0].transcript
            
            logger.info(f"Successfully transcribed audio ({len(transcription)} chars)")
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing speech: {str(e)}")
            raise
    
    def transcribe_audio_file(self, file_path, language_code="en-US"):
        """Transcribe an audio file
        
        Args:
            file_path: Path to the audio file
            language_code: Language code for transcription
            
        Returns:
            Transcribed text
        """
        try:
            # Read the audio file
            with open(file_path, "rb") as audio_file:
                audio_content = audio_file.read()
            
            # Transcribe the audio
            return self.speech_to_text(audio_content, language_code)
        except Exception as e:
            logger.error(f"Error transcribing audio file {file_path}: {str(e)}")
            raise
    
    def transcribe_audio_data(self, audio_data, language_code="en-US"):
        """Transcribe audio data from a request
        
        Args:
            audio_data: Binary audio data from request
            language_code: Language code for transcription
            
        Returns:
            Transcribed text
        """
        try:
            # Convert audio if necessary (support different formats)
            # For now, we assume the audio is already in the right format
            
            # Transcribe the audio
            return self.speech_to_text(audio_data, language_code)
        except Exception as e:
            logger.error(f"Error transcribing audio data: {str(e)}")
            raise
    
    def process_command(self, audio_data, language_code="en-US"):
        """Process a voice command
        
        Args:
            audio_data: Binary audio data of the command
            language_code: Language code for transcription
            
        Returns:
            Dictionary with command info
        """
        try:
            # Transcribe the audio
            text = self.transcribe_audio_data(audio_data, language_code)
            
            # Simple command detection logic
            commands = {
                "read": ["read", "speak", "say", "tell me"],
                "summarize": ["summarize", "summary", "analyze", "analysis"],
                "reply": ["reply", "respond", "answer"],
                "forward": ["forward", "send to"],
                "delete": ["delete", "remove", "trash"],
                "mark": ["mark", "flag", "star"],
                "help": ["help", "assist", "support"]
            }
            
            # Detect command type
            command_type = None
            text_lower = text.lower()
            
            for cmd, keywords in commands.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        command_type = cmd
                        break
                if command_type:
                    break
            
            # Return the result
            return {
                "text": text,
                "command_type": command_type or "unknown",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return {
                "text": "",
                "command_type": "error",
                "success": False,
                "error": str(e)
            }
