# This file makes the views directory a Python package 

# Auth views
from .auth_views import login_view, logout_view, serve_login

# Core views
from .core_views import (
    compose, sent_email, spam_email,
    settings_view as settings,  # Alias settings_view to settings
    get_gmail_auth, upload_excel
)

# Gmail views
from .gmail_views import (
    authenticate_gmail, gmail_callback, sync_emails_view as sync_emails,
    send_email
)

# Email views
from .email_views import (
    inbox_email_detail, inbox_email, delete_email
)

# Dashboard views
from .dashboard_views import priority_dashboard, email_dashboard, get_dashboard_data

# AI views
from .ai_views import (
    analyze_email, store_email_embedding, similar_emails,
    suggest_reply, daily_summary
)

# Voice views
from .voice_views import (
    text_to_speech, speech_to_text, process_voice_command,
    available_voices, read_email, process_reply, process_forward, process_compose
)

__all__ = [
    # Auth views
    'login_view', 'logout_view', 'serve_login',
    
    # Core views
    'compose', 'sent_email', 'spam_email',
    'settings', 'get_gmail_auth', 'upload_excel',
    
    # Gmail views
    'authenticate_gmail', 'gmail_callback', 'sync_emails', 'send_email',
    
    # Email views
    'inbox_email_detail', 'inbox_email', 'delete_email',
    
    # Dashboard views
    'priority_dashboard', 'email_dashboard', 'get_dashboard_data',
    
    # AI views
    'analyze_email', 'store_email_embedding', 'similar_emails',
    'suggest_reply', 'daily_summary',
    
    # Voice views
    'text_to_speech', 'speech_to_text', 'process_voice_command',
    'available_voices', 'read_email', 'process_reply', 'process_forward', 'process_compose'
] 