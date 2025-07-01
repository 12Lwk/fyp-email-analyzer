from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    user_email = models.EmailField(primary_key=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user_email} - {self.display_name or 'No display name'}"

    @property
    def username(self):
        """Get username from email."""
        return self.user_email.split('@')[0] if self.user_email else None

    def get_setting(self, key, default=None):
        """Get a specific setting value."""
        return self.preferences.get(key, default)

    def set_setting(self, key, value):
        """Set a specific setting value."""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
        self.save()

    def get_default_settings(self):
        """Get default settings."""
        return {
            'theme': 'light',
            'notifications_enabled': True,
            'email_per_page': 25,
            'default_font': 'Calibri',
            'auto_save_drafts': True,
            'show_snippets': True,
            'compact_view': False,
            'timezone': 'UTC+8'
        }

    def save(self, *args, **kwargs):
        """Ensure default settings exist."""
        if not self.preferences:
            self.preferences = self.get_default_settings()
        super().save(*args, **kwargs)

class Email(models.Model):
    # Core email fields
    id = models.CharField(max_length=255, primary_key=True)
    user_email = models.EmailField()
    subject = models.CharField(max_length=1000)
    sender = models.EmailField()
    recipients = models.JSONField(default=list)
    date = models.DateTimeField()
    snippet = models.TextField()
    has_attachments = models.BooleanField(default=False)
    attachments = models.JSONField(default=list)
    star = models.BooleanField(default=False)
    label = models.CharField(max_length=50, null=True, blank=True)
    folder = models.CharField(max_length=50, default='INBOX')
    last_modified = models.DateTimeField(auto_now=True)

    # Priority fields
    priority = models.CharField(max_length=20, null=True, blank=True)
    priority_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    priority_explanation = models.TextField(null=True, blank=True)
    priority_last_updated = models.DateTimeField(null=True, blank=True)

    # Category fields
    category = models.CharField(max_length=50, null=True, blank=True)
    category_confidence = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    category_last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'emails'
        indexes = [
            models.Index(fields=['user_email', 'folder']),
            models.Index(fields=['date']),
            models.Index(fields=['priority']),
            models.Index(fields=['category']),
        ]
        unique_together = ['id', 'user_email']
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject} - {self.sender}"

    def save(self, *args, **kwargs):
        """Update last_modified fields when priority or category changes."""
        if self.pk:  # If this is an update
            try:
                old_instance = Email.objects.get(pk=self.pk)
                if old_instance.priority != self.priority:
                    self.priority_last_updated = timezone.now()
                if old_instance.category != self.category:
                    self.category_last_updated = timezone.now()
            except Email.DoesNotExist:
                pass  # This is a new instance
        super().save(*args, **kwargs)

    def clean(self):
        """Validate model fields before saving."""
        if self.priority_score is not None and not 0 <= self.priority_score <= 1:
            raise ValidationError("Priority score must be between 0 and 1")
        if self.category_confidence is not None and not 0 <= self.category_confidence <= 1:
            raise ValidationError("Category confidence must be between 0 and 1")
        if not self.recipients:
            raise ValidationError("At least one recipient is required")
        if not self.sender:
            raise ValidationError("Sender email is required") 