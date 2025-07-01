"""Custom exceptions for AI services."""

class AIServiceError(Exception):
    """Base exception for AI service-related errors."""
    def __init__(self, message: str = "An error occurred in the AI service", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class ModelNotReadyError(AIServiceError):
    """Exception raised when an AI model is not ready or failed to initialize."""
    def __init__(self, message: str = "AI model is not ready or failed to initialize", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class EmbeddingError(AIServiceError):
    """Exception raised when there's an error generating or processing embeddings."""
    def __init__(self, message: str = "Error processing embeddings", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class SummarizationError(AIServiceError):
    """Exception raised when there's an error generating summaries."""
    def __init__(self, message: str = "Error generating summary", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class RecommendationError(AIServiceError):
    """Exception raised when there's an error generating recommendations."""
    def __init__(self, message: str = "Error generating recommendations", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class InvalidInputError(AIServiceError):
    """Exception raised when input to an AI service is invalid."""
    def __init__(self, message: str = "Invalid input provided to AI service", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class ServiceTimeoutError(AIServiceError):
    """Exception raised when an AI service operation times out."""
    def __init__(self, message: str = "AI service operation timed out", *args, **kwargs):
        super().__init__(message, *args, **kwargs) 