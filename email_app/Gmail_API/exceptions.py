class GmailAPIError(Exception):
    """Base exception class for Gmail API related errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class GmailAuthError(GmailAPIError):
    """Exception raised when there are authentication issues with Gmail API."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class GmailServiceError(GmailAPIError):
    """Exception raised when there are issues with Gmail service initialization."""
    def __init__(self, message: str = "Failed to initialize Gmail service"):
        super().__init__(message, status_code=500)

class GmailMessageError(GmailAPIError):
    """Exception raised when there are issues with message operations."""
    def __init__(self, message: str = "Failed to process message"):
        super().__init__(message, status_code=400)

class GmailRateLimitError(GmailAPIError):
    """Exception raised when Gmail API rate limits are exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)

class GmailQuotaExceededError(GmailAPIError):
    """Exception raised when Gmail API quota is exceeded."""
    def __init__(self, message: str = "API quota exceeded"):
        super().__init__(message, status_code=403) 