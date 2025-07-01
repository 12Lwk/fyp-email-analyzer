import os
import logging
import io
import base64
from typing import Optional, List, Tuple, Dict, Any, Union
import numpy as np
try:
    from pydub import AudioSegment
    from pydub.exceptions import CouldntDecodeError
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
from django.conf import settings
from google.cloud.speech_v1 import SpeechClient
from google.cloud.speech_v1.types import RecognitionAudio, RecognitionConfig
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError

# Import the fallback service
from .audio_service import fallback_service

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Utility for processing audio data"""
    
    @staticmethod
    def is_audio_processing_available() -> bool:
        """Check if audio processing capabilities are available"""
        if not PYDUB_AVAILABLE:
            return False
        return fallback_service.is_ffmpeg_available()
    
    @staticmethod
    def convert_audio_format(audio_data: bytes, source_format: str, 
                           target_format: str = "wav") -> Optional[bytes]:
        """Convert audio between formats
        
        Args:
            audio_data: Binary audio data
            source_format: Source format (mp3, wav, etc.)
            target_format: Target format (mp3, wav, etc.)
            
        Returns:
            Converted audio data or None if failed
        """
        if not AudioProcessor.is_audio_processing_available():
            logger.warning("Audio processing not available. Using fallback service.")
            result = fallback_service.process_audio(audio_data, source_format, target_format)
            return None if not result.get("success", False) else audio_data
            
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
            
            # Export to target format
            buffer = io.BytesIO()
            audio.export(buffer, format=target_format)
            buffer.seek(0)
            
            return buffer.read()
        except CouldntDecodeError as e:
            logger.error(f"Could not decode audio from {source_format}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error converting audio from {source_format} to {target_format}: {str(e)}")
            return None
    
    @staticmethod
    def normalize_audio(audio_data: bytes, source_format: str = "wav") -> Optional[bytes]:
        """Normalize audio volume
        
        Args:
            audio_data: Binary audio data
            source_format: Audio format
            
        Returns:
            Normalized audio data or None if failed
        """
        if not AudioProcessor.is_audio_processing_available():
            logger.warning("Audio processing not available. Cannot normalize audio.")
            return audio_data
            
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
            
            # Normalize to -20dB
            normalized = audio.normalize(headroom=-20.0)
            
            # Export back to original format
            buffer = io.BytesIO()
            normalized.export(buffer, format=source_format)
            buffer.seek(0)
            
            return buffer.read()
        except CouldntDecodeError as e:
            logger.error(f"Could not decode audio for normalization: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error normalizing audio: {str(e)}")
            return None
    
    @staticmethod
    def decode_base64_audio(base64_data: str, audio_format: str = "wav") -> Optional[bytes]:
        """Decode base64 encoded audio
        
        Args:
            base64_data: Base64 encoded audio string
            audio_format: Audio format
            
        Returns:
            Binary audio data or None if failed
        """
        # Use fallback service's decode_base64_audio method which doesn't depend on ffmpeg
        return fallback_service.decode_base64_audio(base64_data)
    
    @staticmethod
    def detect_silence(audio_data: bytes, source_format: str = "wav", 
                      silence_threshold: float = -50.0, 
                      min_silence_len: int = 500) -> List[Tuple[int, int]]:
        """Detect silence in audio
        
        Args:
            audio_data: Binary audio data
            source_format: Audio format
            silence_threshold: Silence threshold in dB
            min_silence_len: Minimum silence length in ms
            
        Returns:
            List of silence intervals (start_ms, end_ms)
        """
        if not AudioProcessor.is_audio_processing_available():
            logger.warning("Audio processing not available. Cannot detect silence.")
            return []
            
        try:
            from pydub.silence import detect_silence
            
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
            
            # Detect silence
            silence_intervals = detect_silence(
                audio, 
                min_silence_len=min_silence_len, 
                silence_thresh=silence_threshold
            )
            
            return silence_intervals
        except CouldntDecodeError as e:
            logger.error(f"Could not decode audio for silence detection: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error detecting silence in audio: {str(e)}")
            return []
    
    @staticmethod
    def trim_silence(audio_data: bytes, source_format: str = "wav") -> Optional[bytes]:
        """Trim silence from the beginning and end of audio
        
        Args:
            audio_data: Binary audio data
            source_format: Audio format
            
        Returns:
            Trimmed audio data or None if failed
        """
        if not AudioProcessor.is_audio_processing_available():
            logger.warning("Audio processing not available. Cannot trim silence.")
            return audio_data
            
        try:
            from pydub.silence import detect_leading_silence
            
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
            
            # Trim silence
            start_trim = detect_leading_silence(audio)
            end_trim = detect_leading_silence(audio.reverse())
            
            duration = len(audio)
            trimmed = audio[start_trim:duration-end_trim]
            
            # Export trimmed audio
            buffer = io.BytesIO()
            trimmed.export(buffer, format=source_format)
            buffer.seek(0)
            
            return buffer.read()
        except CouldntDecodeError as e:
            logger.error(f"Could not decode audio for trimming: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error trimming silence from audio: {str(e)}")
            return None

class CommandProcessor:
    """Utility for processing voice commands"""
    
    @staticmethod
    def extract_intent(text: str) -> Dict[str, Any]:
        """Extract intent from command text
        
        Args:
            text: Command text
            
        Returns:
            Dictionary with intent information
        """
        text_lower = text.lower()
        
        # Command patterns
        patterns = {
            'read_email': ['read email', 'read the email', 'read message'],
            'summarize': ['summarize', 'summary', 'give me a summary'],
            'reply': ['reply', 'respond', 'write a response'],
            'delete': ['delete', 'remove', 'trash'],
            'forward': ['forward', 'send to', 'share with'],
            'help': ['help', 'what can you do', 'commands', 'options']
        }
        
        # Default result
        result = {
            'intent': 'unknown',
            'confidence': 0.0,
            'entities': {}
        }
        
        # Check for intent matches
        for intent, phrases in patterns.items():
            for phrase in phrases:
                if phrase in text_lower:
                    result['intent'] = intent
                    # Simple confidence - can be improved
                    result['confidence'] = 0.8
                    break
        
        # Extract entities
        if result['intent'] != 'unknown':
            # Extract recipient for forward intent
            if result['intent'] == 'forward' and 'to' in text_lower:
                parts = text_lower.split('to')
                if len(parts) > 1:
                    recipient = parts[1].strip()
                    result['entities']['recipient'] = recipient
        
        return result
    
    @staticmethod
    def generate_response(intent_data: Dict[str, Any]) -> str:
        """Generate response for a voice command intent
        
        Args:
            intent_data: Intent data from extract_intent
            
        Returns:
            Response text
        """
        intent = intent_data.get('intent', 'unknown')
        
        # Response templates
        responses = {
            'read_email': "Reading the email content for you.",
            'summarize': "Generating a summary of this email.",
            'reply': "Preparing a reply to this email.",
            'delete': "Do you want to delete this email?",
            'forward': "Preparing to forward this email.",
            'help': "I can read emails, summarize content, help you reply, delete or forward messages. What would you like me to do?",
            'unknown': "I'm not sure what you want me to do. You can ask me to read, summarize, reply to, delete or forward an email."
        }
        
        # Add entity information if available
        response = responses.get(intent, responses['unknown'])
        
        if intent == 'forward' and 'recipient' in intent_data.get('entities', {}):
            recipient = intent_data['entities']['recipient']
            response = f"Preparing to forward this email to {recipient}."
        
        return response

class SpeechToTextService:
    """Utility for speech-to-text conversion"""
    
    def __init__(self) -> None:
        # Get credentials file path
        credentials_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'demo_speech_to_text_account.json'
        )
        
        # Alternative paths to try
        alt_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VOICE_ENABLE', 'demo_speech_to_text_account.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'voice_services', 'demo_speech_to_text_account.json'),
            os.path.join(settings.BASE_DIR, 'email_app', 'voice_services', 'demo_speech_to_text_account.json')
        ]
        
        # Try all paths until we find one
        for path in [credentials_path] + alt_paths:
            if os.path.exists(path):
                credentials_path = path
                break
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            logger.error(f"Speech-to-text credentials file not found at: {credentials_path}")
            logger.error("Speech-to-text functionality will be limited")
            self.client = None
            return
        
        # Load credentials
        try:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = SpeechClient(credentials=self.credentials)
            logger.info("Speech-to-text service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize speech-to-text client: {str(e)}")
            self.client = None
    
    def speech_to_text(self, audio_content: bytes, 
                      language_code: str = "en-US") -> Optional[str]:
        """Convert speech to text
        
        Args:
            audio_content: Audio content bytes
            language_code: Language code
            
        Returns:
            Transcript text or None if failed
        """
        if self.client is None:
            logger.error("Speech-to-text client not initialized")
            return None
            
        try:
            # Create audio object
            audio = RecognitionAudio(content=audio_content)
            
            # Configure speech recognition
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True
            )
            
            # Perform speech recognition
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract transcript
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            return transcript
        except GoogleAPIError as e:
            logger.error(f"Google API error in speech-to-text: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            return None
    
    def process_audio_file(self, file_path: str) -> Optional[str]:
        """Process an audio file and convert to text
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Read audio file
            with open(file_path, 'rb') as audio_file:
                audio_content = audio_file.read()
            
            # Convert to text
            return self.speech_to_text(audio_content)
        except Exception as e:
            logger.error(f"Error processing audio file: {str(e)}")
            return None
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages
        
        Returns:
            List of dictionaries containing language information
        """
        if self.client is None:
            logger.error("Speech-to-text client not initialized")
            return []
        
        try:
            response = self.client.list_languages()
            languages: List[Dict[str, Any]] = []
            
            for language in response.languages:
                languages.append({
                    'code': language.language_code,
                    'name': language.display_name
                })
            
            return languages
        except GoogleAPIError as e:
            logger.error(f"Google STT API error getting languages: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting supported languages: {str(e)}")
            return []

class VoiceUtils:
    """Main utility class for voice processing"""
    AudioProcessor = AudioProcessor
    CommandProcessor = CommandProcessor
    SpeechToTextService = SpeechToTextService
