from typing import Dict, List, Final, Tuple, Any
from pathlib import Path
import os

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Email Configuration Constants
MAX_RESULTS: Final[int] = 100
DEFAULT_FOLDER: Final[str] = 'INBOX'
ATTACHMENT_MIME_TYPE: Final[Tuple[str, str]] = ('application', 'octet-stream')
CSV_DIRECTORY: Final[str] = 'email_exports'

# Email Configuration
EMAIL_COLUMNS: Final[List[str]] = [
    'id', 'user_email', 'subject', 'sender', 'recipients',
    'date', 'snippet', 'has_attachments', 'attachments',
    'star', 'label', 'folder', 'last_modified', 'priority',
    'category', 'embedding'
]

# Error Messages
ERROR_MESSAGES: Final[Dict[str, str]] = {
    'auth_required': 'Authentication required',
    'auth_failed': 'Authentication failed',
    'invalid_request': 'Invalid request',
    'method_not_allowed': 'Method not allowed',
    'no_file': 'No file uploaded',
    'db_error': 'Database error',
    'email_not_found': 'Email not found',
    'processing_error': 'Error processing request',
    'ai_service_error': 'AI service error',
    'ai_analysis_error': 'Error analyzing email',
    'tts_error': 'Text-to-speech error',
    'stt_error': 'Speech-to-text error',
    'audio_processing_error': 'Audio processing error',
    'RENDER_ERROR': 'Error rendering the page'
}

# HTTP Status Codes
HTTP_STATUS: Final[Dict[str, int]] = {
    'ok': 200,
    'created': 201,
    'accepted': 202,
    'no_content': 204,
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'method_not_allowed': 405,
    'conflict': 409,
    'gone': 410,
    'unprocessable_entity': 422,
    'too_many_requests': 429,
    'server_error': 500,
    'bad_gateway': 502,
    'service_unavailable': 503
}

# Email Categories
EMAIL_CATEGORIES: Final[List[str]] = [
    'Work',
    'Personal',
    'Finance',
    'Shopping',
    'Travel',
    'Social',
    'Updates',
    'Promotions',
    'Spam',
    'Other'
]

# Priority Levels
PRIORITY_LEVELS: Final[List[str]] = [
    'High',
    'Medium',
    'Low'
]

# Gmail API Configuration
GMAIL_API_CONFIG: Final[Dict[str, str]] = {
    'credentials_path': os.path.join(BASE_DIR, 'GMAIL_API', 'credentials.json'),
    'token_path': os.path.join(BASE_DIR, 'GMAIL_API', 'token.json'),
    'scopes': ['https://www.googleapis.com/auth/gmail.modify']
}

# Database Configuration
DB_CONFIG: Final[Dict[str, str]] = {
    'dbname': 'email_db',
    'user': 'postgres',
    'password': 'email1234',
    'host': 'localhost',
    'port': '5432'
}

# AI Service Configuration
AI_CONFIG: Final[Dict[str, Any]] = {
    'timeout': 10,  # seconds
    'max_retries': 3,
    'batch_size': 50,
    'cache_ttl': 3600,  # 1 hour
    'models': {
        'gemini': {
            'model_name': 'gemini-pro',
            'temperature': 0.7,
            'max_output_tokens': 2048,
            'top_p': 0.8,
            'top_k': 40
        },
        'embedding': {
            'model_name': 'gemini-embed',
            'batch_size': 100,
            'dimension': 768
        }
    },
    'safety_settings': {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_MEDIUM_AND_ABOVE'
    }
}

# Logging Configuration
LOG_CONFIG: Final[Dict[str, Any]] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'email_app.log'),
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'email_app': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# Gmail API Settings
GMAIL_SETTINGS: Final[Dict[str, Any]] = {
    'api_version': 'v1',
    'scopes': [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ],
    'credentials_file': os.path.join('GMAIL_API', 'credentials.json'),
    'token_file': os.path.join('GMAIL_API', 'token.json')
}

# AI Service Settings
AI_SETTINGS: Final[Dict[str, Any]] = {
    'embedding_dimension': 384,
    'max_tokens': 1000,
    'temperature': 0.7,
    'top_p': 0.9,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

# Voice Service Settings
VOICE_SETTINGS: Final[Dict[str, Any]] = {
    'default_language': 'en-US',
    'default_voice': 'en-US-Standard-C',
    'sample_rate': 16000,
    'audio_encoding': 'LINEAR16',
    'timeout': 10.0
} 