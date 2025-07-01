"""Email-related models for the email application."""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

User = get_user_model()

# class EmailCategory(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
# 
#     class Meta:
#         verbose_name = "Email Category"
#         verbose_name_plural = "Email Categories"
#         ordering = ['name']
# 
#     def __str__(self):
#         return self.name

class EmailPriority(models.Model):
    """Model for email priority levels.
    
    Attributes:
        name (str): The priority level (High, Medium, Low)
        description (str): Optional description of the priority level
        weight (int): Numerical weight for sorting (1-100)
        created_at (datetime): When this priority was created
        updated_at (datetime): When this priority was last updated
    """
    name = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Priority level (High, Medium, Low)"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the priority level"
    )
    weight = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Numerical weight for sorting (1-100)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this priority was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this priority was last updated"
    )
    
    class Meta:
        """Meta options for EmailPriority model."""
        verbose_name = "Email Priority"
        verbose_name_plural = "Email Priorities"
        ordering = ['-weight']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['weight'])
        ]
    
    def __str__(self) -> str:
        """String representation of the priority level."""
        return self.name

class Email(models.Model):
    """Model for storing email information."""
    gmail_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Gmail message ID"
    )
    id = models.BigAutoField(
        primary_key=True,
        help_text="Internal primary key"
    )
    user = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='emails',
        help_text="User who owns this email"
    )
    subject = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Email subject"
    )
    sender = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Sender's email address and display name"
    )
    recipients = models.JSONField(
        help_text="List of recipient email addresses and display names"
    )
    body = models.TextField(
        blank=True,
        help_text="Email body content"
    )
    date = models.DateTimeField(
        db_index=True,
        help_text="Date and time the email was sent/received"
    )
    snippet = models.TextField(
        blank=True,
        help_text="Short preview of the email content"
    )
    has_attachments = models.BooleanField(
        default=False,
        help_text="Whether the email has attachments"
    )
    folder = models.CharField(
        max_length=50,
        default='INBOX',
        db_index=True,
        help_text="Gmail folder (INBOX, SENT, etc.)"
    )
    labels = models.JSONField(
        default=list,
        help_text="List of Gmail labels"
    )
    category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Email category for organization (e.g., 'Work', 'Finance')"
    )
    priority = models.ForeignKey(
        'EmailPriority',
        on_delete=models.SET_NULL,
        null=True,
        db_index=True,
        help_text="Email priority level"
    )
    search_text = models.TextField(
        blank=True,
        help_text="Concatenated text for full-text search"
    )
    search_vector = SearchVectorField(
        null=True,
        help_text="Optimized vector for full-text search"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['folder']),
            models.Index(fields=['category']),
            models.Index(fields=['priority']),
            GinIndex(fields=['search_vector'])
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject} ({self.date})"

    def update_search_vector(self):
        """Update the search vector with the latest content."""
        search_text = f"{self.subject} {self.sender} {self.body} {self.snippet}"
        self.search_text = search_text
        # The trigger will handle updating search_vector
        self.save()

class EmailAttachment(models.Model):
    """Model for storing email attachment information."""
    id = models.BigAutoField(
        primary_key=True,
        help_text="Internal primary key"
    )
    email = models.ForeignKey(
        Email,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Email this attachment belongs to"
    )
    filename = models.CharField(
        max_length=255,
        help_text="Original filename of the attachment"
    )
    mime_type = models.CharField(
        max_length=100,
        help_text="MIME type of the attachment"
    )
    size = models.BigIntegerField(
        help_text="Size of the attachment in bytes"
    )
    attachment_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Gmail attachment ID"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['mime_type'])
        ]

    def __str__(self):
        return f"{self.filename} ({self.mime_type})"