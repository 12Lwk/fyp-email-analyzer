# This file makes the models directory a Python package
from .user_models import UserProfile
from .email_models import Email, EmailAttachment, EmailPriority

__all__ = [
    'UserProfile',
    'Email',
    'EmailAttachment',
    'EmailPriority',
] 