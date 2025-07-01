import os
import logging
import io
from typing import Optional, Union, Dict, Any
import base64

logger = logging.getLogger(__name__)

class FallbackAudioService:
    """
    Fallback audio processing service that doesn't depend on ffmpeg.
    This is used when ffmpeg is not installed on the system.
    """
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if ffmpeg is available on the system path"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   check=False)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
    
    @staticmethod
    def process_audio(audio_data: bytes, source_format: str = "wav",
                    target_format: str = "wav") -> Dict[str, Any]:
        """
        Process audio without ffmpeg dependency.
        Returns metadata about the audio but doesn't process it.
        
        Args:
            audio_data: Binary audio data
            source_format: Source audio format
            target_format: Target audio format
            
        Returns:
            Dictionary with audio info
        """
        if not FallbackAudioService.is_ffmpeg_available():
            logger.warning("FFmpeg not available. Audio processing functionality is limited.")
            
        return {
            "success": False,
            "error": "FFmpeg not available for audio processing",
            "source_format": source_format,
            "target_format": target_format,
            "size": len(audio_data) if audio_data else 0,
            "processed": False
        }
    
    @staticmethod
    def decode_base64_audio(base64_data: str) -> Optional[bytes]:
        """Decode base64 encoded audio
        
        Args:
            base64_data: Base64 encoded audio string
            
        Returns:
            Binary audio data or None if failed
        """
        try:
            # Remove data URL prefix if present
            if 'base64,' in base64_data:
                base64_data = base64_data.split('base64,')[1]
            
            # Decode base64
            audio_data = base64.b64decode(base64_data)
            
            return audio_data
        except (base64.binascii.Error, ValueError) as e:
            logger.error(f"Invalid base64 data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error decoding base64 audio data: {str(e)}")
            return None

# Create a fallback service instance
fallback_service = FallbackAudioService()
