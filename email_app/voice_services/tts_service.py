import os
import logging
import json
from typing import Optional, List, Dict, Any, BinaryIO, Union
from google.cloud import texttospeech
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError
from django.conf import settings
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """Service for converting text to speech using Google Cloud TTS"""
    
    def __init__(self) -> None:
        # Get credentials file path
        credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'VOICE_ENABLE',
            'demo_text_to_speech_account.json'
        )
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            logger.error(f"TTS credentials file not found at: {credentials_path}")
            raise FileNotFoundError(f"TTS credentials file not found at: {credentials_path}")
        
        # Load credentials
        try:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = texttospeech.TextToSpeechClient(credentials=self.credentials)
            logger.info("Text-to-Speech service initialized")
        except (GoogleAPIError, ValueError) as e:
            logger.error(f"Failed to initialize TTS client: {str(e)}")
            raise
    
    def text_to_speech(self, text: str, voice_name: str = "en-US-Standard-C", 
                      language_code: str = "en-US") -> Optional[bytes]:
        """Convert text to speech
        
        Args:
            text: The text to convert to speech
            voice_name: Name of the voice to use
            language_code: Language code for the voice
            
        Returns:
            Binary audio content or None if failed
        """
        try:
            # Process long text by splitting into chunks if needed
            if len(text) > 5000:
                return self._process_long_text(text, voice_name, language_code)
            
            # Set text input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Set voice parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            # Set audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Generate speech
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
        except GoogleAPIError as e:
            logger.error(f"Google TTS API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return None
    
    def _process_long_text(self, text: str, voice_name: str, 
                          language_code: str) -> Optional[bytes]:
        """Process text that exceeds TTS length limits
        
        Args:
            text: The long text to process
            voice_name: Name of the voice to use
            language_code: Language code for the voice
            
        Returns:
            Combined audio content or None if failed
        """
        logger.info(f"Processing long text ({len(text)} chars) for TTS")
        
        # Split text into chunks of 5000 characters
        # Try to split at sentence boundaries
        chunks: List[str] = []
        current_chunk = ""
        
        # Sentence-ending punctuation
        sentence_endings = ['.', '!', '?', '\n\n']
        
        for i, char in enumerate(text):
            current_chunk += char
            
            # Check if we have a full chunk
            if len(current_chunk) >= 4800:  # Slightly less than 5000 for safety
                # Look ahead for a sentence ending
                look_ahead = text[i:i+200] if i+200 < len(text) else text[i:]
                
                end_pos = -1
                for ending in sentence_endings:
                    pos = look_ahead.find(ending)
                    if pos != -1 and (end_pos == -1 or pos < end_pos):
                        end_pos = pos
                
                if end_pos != -1:
                    # Include the sentence ending and the character after it
                    end_pos = min(end_pos + 2, len(look_ahead))
                    chunks.append(current_chunk + look_ahead[:end_pos])
                    current_chunk = ""
                    # Skip the characters we just added
                    text = text[:i+1] + text[i+1+end_pos:]
                    i += end_pos
                else:
                    # No good breaking point found, just split at current position
                    chunks.append(current_chunk)
                    current_chunk = ""
        
        # Add any remaining text
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Split text into {len(chunks)} chunks for TTS")
        
        # Process each chunk and combine audio
        combined = AudioSegment.empty()
        
        for i, chunk in enumerate(chunks):
            try:
                logger.debug(f"Processing TTS chunk {i+1}/{len(chunks)}")
                audio_content = self.text_to_speech(chunk, voice_name, language_code)
                if audio_content is None:
                    logger.error(f"Failed to process chunk {i+1}")
                    continue
                
                # Convert to AudioSegment
                chunk_audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
                
                # Add to combined audio
                combined += chunk_audio
            except Exception as e:
                logger.error(f"Error processing TTS chunk {i+1}: {str(e)}")
                # Continue with other chunks
        
        if len(combined) == 0:
            logger.error("No audio was generated from the chunks")
            return None
        
        # Export combined audio to bytes
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        buffer.seek(0)
        
        return buffer.read()
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available TTS voices
        
        Returns:
            List of dictionaries containing voice information
        """
        try:
            response = self.client.list_voices()
            voices: List[Dict[str, Any]] = []
            
            for voice in response.voices:
                for language_code in voice.language_codes:
                    if language_code.startswith('en'):  # Only include English voices
                        voices.append({
                            'name': voice.name,
                            'language_code': language_code,
                            'gender': texttospeech.SsmlVoiceGender(voice.ssml_gender).name
                        })
            
            return voices
        except GoogleAPIError as e:
            logger.error(f"Google TTS API error getting voices: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []
