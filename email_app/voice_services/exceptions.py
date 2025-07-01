"""Voice service exceptions."""

class VoiceServiceError(Exception):
    """Base class for voice service errors."""
    pass

class TTSError(VoiceServiceError):
    """Text-to-speech service error."""
    pass

class STTError(VoiceServiceError):
    """Speech-to-text service error."""
    pass

class AudioProcessingError(VoiceServiceError):
    """Audio processing error."""
    pass 