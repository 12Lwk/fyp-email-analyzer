"""User-related models for the email application."""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile information.
    
    Attributes:
        user (User): Django user this profile belongs to
        email (str): User's email address
        gmail_connected (bool): Whether Gmail is connected
        last_sync (datetime): Last Gmail sync timestamp
        email_signature (str): User's email signature
        preferences (dict): User preferences and settings
        created_at (datetime): When this profile was created
        updated_at (datetime): When this profile was last updated
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        db_index=True,
        help_text="Django user this profile belongs to"
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="User's email address"
    )
    gmail_connected = models.BooleanField(
        default=False,
        help_text="Whether Gmail is connected"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last Gmail sync timestamp"
    )
    email_signature = models.TextField(
        blank=True,
        help_text="User's email signature"
    )
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences and settings"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this profile was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this profile was last updated"
    )
    
    class Meta:
        """Meta options for UserProfile model."""
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['email'])
        ]
    
    def __str__(self) -> str:
        """String representation of the user profile."""
        return f"{self.user.username}'s profile"

class UserSettings(models.Model):
    """User-specific application settings.
    
    Attributes:
        user (User): Django user these settings belong to
        auto_categorize (bool): Whether to auto-categorize emails
        auto_priority (bool): Whether to auto-set email priority
        voice_enabled (bool): Whether voice commands are enabled
        notification_enabled (bool): Whether notifications are enabled
        theme (str): UI theme preference
        language (str): Language preference
        ai_settings (dict): AI-related settings and preferences
        created_at (datetime): When these settings were created
        updated_at (datetime): When these settings were last updated
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
        db_index=True,
        help_text="Django user these settings belong to"
    )
    auto_categorize = models.BooleanField(
        default=True,
        help_text="Whether to auto-categorize emails"
    )
    auto_priority = models.BooleanField(
        default=True,
        help_text="Whether to auto-set email priority"
    )
    voice_enabled = models.BooleanField(
        default=False,
        help_text="Whether voice commands are enabled"
    )
    notification_enabled = models.BooleanField(
        default=True,
        help_text="Whether notifications are enabled"
    )
    theme = models.CharField(
        max_length=20,
        default='light',
        validators=[MinLengthValidator(4)],
        help_text="UI theme preference"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        validators=[MinLengthValidator(2)],
        help_text="Language preference"
    )
    ai_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-related settings and preferences"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When these settings were created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When these settings were last updated"
    )
    
    class Meta:
        """Meta options for UserSettings model."""
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['theme']),
            models.Index(fields=['language'])
        ]
    
    def __str__(self) -> str:
        """String representation of the user settings."""
        return f"{self.user.username}'s settings"

@receiver(post_save, sender=User)
def create_user_profile_and_settings(sender, instance: User, created: bool, **kwargs) -> None:
    """Create user profile and settings when a new user is created.
    
    Args:
        sender: The model class (User)
        instance: The actual user instance being saved
        created: Whether this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Create profile with default preferences
        UserProfile.objects.create(
            user=instance,
            email=instance.email,
            preferences={
                'notifications': {
                    'email': True,
                    'desktop': True,
                    'mobile': False
                },
                'display': {
                    'emails_per_page': 50,
                    'sort_order': '-date',
                    'timezone': 'UTC'
                }
            }
        )
        
        # Create settings with default AI settings
        UserSettings.objects.create(
            user=instance,
            ai_settings={
                'summarization': {
                    'enabled': True,
                    'max_length': 200
                },
                'categorization': {
                    'enabled': True,
                    'confidence_threshold': 0.8
                },
                'priority': {
                    'enabled': True,
                    'confidence_threshold': 0.7
                }
            }
        ) 