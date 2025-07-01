import logging
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.core.files.uploadedfile import UploadedFile
from typing import Dict, Any, Union, List, Optional
from django.conf import settings
from django.utils import timezone
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from googleapiclient.discovery import build
from django.urls import reverse

# Define the scope for Gmail OAuth2
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://mail.google.com/'
]

# Local imports using relative paths
from ..GMAIL_API.gmail_api import GmailAPI
from ..GMAIL_API.gmail_auth import GmailAuth
from ..GMAIL_API.exceptions import GmailAuthError, GmailAPIError
from ..utils.email_processor import process_message, sync_emails
from ..utils.database.db_utils import get_db_connection
from ..utils.models.check_categories import check_categories
from ..utils.models.model_feedback_handler import ModelFeedbackHandler
from ..utils import VectorDB
from ..ai_services import EmailCategorizationService
from ..ai_services.embeddings.embedding_utils import EmbeddingService
from ..ai_services.summarization.summarization_service import SummarizationService
from ..ai_services.recommendations.recommendation_service import RecommendationService
from ..models.email_models import Email, EmailPriority

from ..utils.constants import ERROR_MESSAGES, HTTP_STATUS

logger = logging.getLogger(__name__)

# Initialize services
embedding_service = EmbeddingService()
summarization_service = SummarizationService()
recommendation_service = RecommendationService()
model_feedback_handler = ModelFeedbackHandler(
    model_path=os.path.join(settings.BASE_DIR, 'email_app', 'models', 'ml_models', 'enhanced_email_categorization_model_v4.joblib')
)
vector_db = VectorDB()
categorization_service = EmailCategorizationService()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def authenticate_gmail(request: HttpRequest) -> JsonResponse:
    """Handle Gmail authentication flow."""
    try:
        # Initialize GmailAuth
        gmail_auth = GmailAuth()
        
        # Get the current host
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        
        # Build the redirect URI using the current host
        redirect_uri = f'{protocol}://{host}/gmail/callback/'
        
        logger.info(f"Starting Gmail authentication with redirect URI: {redirect_uri}")
        
        try:
            # Get auth URL using GmailAuth
            auth_url, state = gmail_auth.get_authorization_url(redirect_uri)
            
            # Store state and redirect URI in session
            request.session['oauth_state'] = state
            request.session['oauth_redirect_uri'] = redirect_uri
            request.session.modified = True
            
            logger.info("Successfully initialized authentication flow")
            
            return JsonResponse({
                'status': 'success',
                'auth_url': auth_url
            })
            
        except GmailAuthError as e:
            logger.error(f"Gmail auth error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to authenticate with Gmail. Please try again.'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Gmail authentication error: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error. Please try again.'
        }, status=500)

@csrf_exempt
def gmail_callback(request: HttpRequest) -> HttpResponse:
    """Handle Gmail OAuth2 callback."""
    try:
        # Log request details
        logger.info("Gmail callback received")
        logger.info(f"Query parameters: {request.GET}")
        
        # Check for error in callback
        if 'error' in request.GET:
            error = request.GET.get('error')
            logger.error(f"Error in Gmail callback: {error}")
            messages.error(request, f'Gmail authentication failed: {error}')
            return redirect('email_app:login')

        # Get authorization code and state
        auth_code = request.GET.get('code')
        received_state = request.GET.get('state')
        
        if not auth_code:
            logger.error("No authorization code received")
            messages.error(request, 'Authentication failed: No authorization code received')
            return redirect('email_app:login')

        # Get stored state and redirect URI
        stored_state = request.session.get('oauth_state')
        redirect_uri = request.session.get('oauth_redirect_uri')
        
        logger.info(f"Stored state: {stored_state}, Received state: {received_state}")
        logger.info(f"Redirect URI: {redirect_uri}")
        
        if not stored_state or not redirect_uri:
            logger.error("Missing oauth state or redirect URI in session")
            messages.error(request, 'Authentication session expired. Please try again.')
            return redirect('email_app:login')

        # Verify state
        if received_state != stored_state:
            logger.error("State mismatch")
            messages.error(request, 'Authentication failed: Invalid state')
            return redirect('email_app:login')

        # Initialize GmailAuth
        gmail_auth = GmailAuth()
        
        try:
            # Exchange auth code for credentials
            logger.info("Exchanging auth code for credentials...")
            credentials = gmail_auth.get_credentials_from_code(auth_code, redirect_uri)
            
            if not credentials:
                logger.error("Failed to obtain credentials")
                messages.error(request, 'Failed to obtain Gmail credentials. Please try again.')
                return redirect('email_app:login')

            # Test the credentials
            logger.info("Testing credentials with Gmail API...")
            service = build('gmail', 'v1', credentials=credentials)
            user_info = service.users().getProfile(userId='me').execute()
            
            if not user_info or 'emailAddress' not in user_info:
                logger.error("Failed to get user profile")
                messages.error(request, 'Failed to get Gmail profile. Please try again.')
                return redirect('email_app:login')
            
            # Store user email and credentials in session
            user_email = user_info['emailAddress']
            logger.info(f"Successfully authenticated user: {user_email}")
            
            # Set session persistence
            request.session.set_expiry(604800)  # 7 days in seconds
            
            # Batch all session updates together
            session_updates = {
                'user_email': user_email,
                'gmail_credentials': credentials.to_json(),
                'is_gmail_authenticated': True,
                'last_activity': timezone.now().isoformat()
            }
            
            # Update session in one go
            request.session.update(session_updates)
            request.session.modified = True
            
            # Start email sync
            try:
                logger.info("Starting email sync...")
                sync_count, error_count = sync_emails(service, user_info)
                
                # Update session with sync results
                request.session['sync_results'] = {
                    'success_count': sync_count,
                    'error_count': error_count,
                    'timestamp': timezone.now().isoformat()
                }
                request.session.modified = True
                
                # Set success message
                if sync_count > 0:
                    messages.success(request, f'Successfully connected to Gmail! {sync_count} emails synced.')
                else:
                    messages.success(request, 'Successfully connected to Gmail!')
                
                # Redirect to dashboard
                return redirect('email_app:email_dashboard')
                
            except Exception as sync_error:
                logger.error(f"Email sync error: {str(sync_error)}", exc_info=True)
                messages.warning(request, 'Connected to Gmail, but email sync failed. Please try syncing manually.')
                return redirect('email_app:email_dashboard')
                
        except Exception as e:
            logger.error(f"Gmail authentication error: {str(e)}", exc_info=True)
            messages.error(request, 'Failed to authenticate with Gmail. Please try again.')
            return redirect('email_app:login')
            
    except Exception as e:
        logger.error(f"Unexpected error in Gmail callback: {str(e)}", exc_info=True)
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return redirect('email_app:login')

def get_gmail_service(request):
    """Get Gmail service from session credentials"""
    try:
        # Get credentials from session
        creds_data = request.session.get('gmail_credentials')
        if not creds_data:
            logger.error("No Gmail credentials found in session")
            return None

        # Parse credentials if stored as JSON string
        if isinstance(creds_data, str):
            try:
                creds_data = json.loads(creds_data)
                logger.info("Successfully parsed credentials from JSON string")
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse credentials JSON: {str(je)}")
                return None

        # Create credentials object
        try:
            creds = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
        except Exception as e:
            logger.error(f"Error creating credentials object: {str(e)}", exc_info=True)
            return None

        # Build Gmail service
        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Error building Gmail service: {str(e)}", exc_info=True)
            return None
            
    except Exception as e:
        logger.error(f"Error in get_gmail_service: {str(e)}", exc_info=True)
        return None

@login_required
def sync_emails_view(request) -> JsonResponse:
    """View for manually triggering email sync"""
    try:
        # Get Gmail service
        service = get_gmail_service(request)
        if not service:
            return JsonResponse({
                'status': 'error',
                'message': 'Gmail service not available. Please authenticate first.'
            })

        # Start sync
        success_count, error_count = sync_emails(service, request.user.userprofile)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Sync completed. Success: {success_count}, Errors: {error_count}'
        })
        
    except Exception as e:
        logger.error(f"Email sync error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Sync failed: {str(e)}'
        })

@login_required(login_url='email_app:login')
def send_email(request: HttpRequest) -> JsonResponse:
    """Send email through Gmail API."""
    if request.method != 'POST':
        return JsonResponse({
            'error': ERROR_MESSAGES['method_not_allowed']
        }, status=HTTP_STATUS['method_not_allowed'])
    
    try:
        # Validate required fields
        required_fields = ['to', 'subject', 'content']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': f"Missing required fields: {', '.join(missing_fields)}"
            }, status=HTTP_STATUS['bad_request'])
            
        # Get attachments
        attachments: List[UploadedFile] = request.FILES.getlist('attachments', [])
        
        # Get Gmail service from session
        service = request.session.get('gmail_service')
        if not service:
            return JsonResponse({'error': 'Gmail service not initialized'}, status=500)
            
        # Create message
        message = MIMEMultipart()
        message['to'] = request.POST['to']
        message['subject'] = request.POST['subject']
        
        # Set the sender (From) address to the user's email
        user_email = request.session.get('user_email', '')
        if user_email:
            message['from'] = user_email
            logger.info(f"Setting sender email to: {user_email}")
        else:
            logger.warning("No user email in session, sender may not be properly set")
        
        # Add body
        body = MIMEText(request.POST['content'])
        message.attach(body)
        
        # Add attachments
        for attachment in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={attachment.name}'
            )
            message.attach(part)
        
        # Convert to raw message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"Successfully sent email to {request.POST['to']}")
        return JsonResponse({
            'status': 'success',
            'message': 'Email sent successfully',
            'message_id': sent_message['id']
        })
        
    except GmailAPIError as e:
        logger.error(f"Gmail API error sending email: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['email_send_failed'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_gateway'])
    except ValueError as e:
        logger.error(f"Invalid email data: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@login_required
def email_dashboard(request: HttpRequest) -> HttpResponse:
    """Render the email dashboard."""
    try:
        # Check if Gmail credentials exist
        gmail_credentials = request.session.get('gmail_credentials')
        if not gmail_credentials:
            return redirect('email_app:login')
        
        # Parse credentials if needed and initialize service
        try:    
            # Parse if stored as string
            if isinstance(gmail_credentials, str):
                gmail_credentials = json.loads(gmail_credentials)
                
            # Create Credentials object
            credentials = Credentials(
                token=gmail_credentials['token'],
                refresh_token=gmail_credentials['refresh_token'],
                token_uri=gmail_credentials['token_uri'],
                client_id=gmail_credentials['client_id'],
                client_secret=gmail_credentials['client_secret'],
                scopes=gmail_credentials['scopes']
            )
            
            # Check if credentials are expired and refresh if needed
            if credentials.expired:
                logger.info("Credentials expired, refreshing...")
                credentials.refresh(Request())
                # Save refreshed credentials
                request.session['gmail_credentials'] = credentials.to_json()
                request.session.modified = True
            
            # Initialize Gmail API
            gmail_api = GmailAPI(credentials=credentials)
            
            # Store service in session
            service = build('gmail', 'v1', credentials=credentials)
            request.session['gmail_service'] = service
            
        except Exception as cred_error:
            logger.error(f"Error setting up Gmail credentials: {str(cred_error)}", exc_info=True)
            messages.error(request, 'Failed to authenticate with Gmail. Please log in again.')
            return redirect('email_app:login')
        
        # Get user email if not in session
        if 'user_email' not in request.session:
            user_info = gmail_api.get_user_profile()
            if user_info and 'emailAddress' in user_info:
                request.session['user_email'] = user_info['emailAddress']
        
        # Initialize sync_data
        sync_data = None
        
        # Sync initial batch of emails
        sync_result = sync_emails_view(request)
        if isinstance(sync_result, JsonResponse):
            sync_data = json.loads(sync_result.content.decode('utf-8'))
            if sync_data.get('status') == 'error':
                messages.error(request, sync_data.get('message', 'Failed to sync emails'))
        
        # Get emails from database
        user_email = request.session.get('user_email', '')
        emails = Email.objects.filter(user_email=user_email).order_by('-date')[:50]
        
        context = {
            'user_email': user_email,
            'emails': emails,
            'sync_status': sync_data
        }
        
        return render(request, 'email_app/email_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        messages.error(request, 'Failed to load dashboard. Please try again.')
        return redirect('email_app:login')

def check_gmail_auth(request: HttpRequest) -> JsonResponse:
    """Check if Gmail authentication is valid and return status."""
    try:
        # Get Gmail service
        service = get_gmail_service(request)
        if not service:
            return JsonResponse({
                'status': 'error',
                'authenticated': False,
                'message': 'Gmail service not available. Please authenticate first.'
            })
            
        # Test the service
        try:
            user_info = service.users().getProfile(userId='me').execute()
            if not user_info or 'emailAddress' not in user_info:
                return JsonResponse({
                    'status': 'error',
                    'authenticated': False,
                    'message': 'Failed to get Gmail profile. Please authenticate again.'
                })
                
            # Authentication is valid
            return JsonResponse({
                'status': 'success',
                'authenticated': True,
                'email': user_info['emailAddress']
            })
            
        except Exception as e:
            logger.error(f"Gmail API error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'authenticated': False,
                'message': 'Gmail API error. Please authenticate again.'
            })
            
    except Exception as e:
        logger.error(f"Error checking Gmail auth: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'authenticated': False,
            'message': 'Failed to check Gmail authentication.'
        })

@csrf_exempt
@require_http_methods(["POST"])
def send_email_api(request: HttpRequest) -> JsonResponse:
    """Send email through Gmail API from AJAX request.
    
    This endpoint handles JSON requests from the frontend to send emails
    via the Gmail API with proper OAuth2 authentication.
    """
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['to', 'subject', 'body']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': f"Missing required fields: {', '.join(missing_fields)}"
            }, status=HTTP_STATUS['bad_request'])
        
        # Enhanced recipient validation
        recipient = data.get('to', '').strip()
        if not recipient or '@' not in recipient:
            logger.warning(f"Invalid recipient format: {recipient}")
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': "Invalid recipient email address format"
            }, status=HTTP_STATUS['bad_request'])
        
        # Get Gmail service
        service = get_gmail_service(request)
        if not service:
            # Try to refresh auth
            logger.info("Gmail service not available. Redirecting to authentication.")
            return JsonResponse({
                'error': 'Gmail authentication required',
                'details': 'Please authenticate with Gmail first.',
                'redirect': '/gmail/authenticate/'
            }, status=HTTP_STATUS['unauthorized'])
        
        # Create message
        message = MIMEMultipart()
        message['to'] = data['to']
        message['subject'] = data['subject']
        
        # Set the sender (From) address to the user's email
        user_email = request.session.get('user_email', '')
        if user_email:
            message['from'] = user_email
            logger.info(f"Setting sender email to: {user_email}")
        else:
            logger.warning("No user email in session, sender may not be properly set")
        
        # Add CC and BCC if provided
        if data.get('cc'):
            message['cc'] = data['cc']
        if data.get('bcc'):
            message['bcc'] = data['bcc']
        
        # Add body - support both plain text and HTML with proper formatting
        if data.get('body_html'):
            # Already formatted as HTML by frontend
            html_content = data.get('body_html')
            
            # Wrap content in a proper HTML email template
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style>
        body {{ 
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        p {{ margin: 0 0 16px 0; padding: 0; }}
        .signature {{ 
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
        }}
        .quote {{
            margin: 20px 0;
            padding-left: 16px;
            border-left: 4px solid #ccc;
            color: #555;
        }}
    </style>
</head>
<body>
    <div>{html_content}</div>
</body>
</html>'''
            
            # Create HTML part
            body = MIMEText(html_content, 'html', 'utf-8')
        else:
            # Format plain text to HTML with full document structure
            # Convert common email text patterns to proper HTML
            content = data['body']
            
            # Handle quoted text (lines starting with >)
            content = content.replace('\n>', '\n<div class="quote">')
            if '\n<div class="quote">' in content:
                content = content.replace('\n<div class="quote">', '\n<div class="quote">') + '</div>'
            
            # Convert plain text to paragraphs
            paragraphs = []
            current_paragraph = []
            
            for line in content.split('\n'):
                if line.strip() == '':
                    if current_paragraph:
                        paragraphs.append('<p>' + '<br>'.join(current_paragraph) + '</p>')
                        current_paragraph = []
                else:
                    current_paragraph.append(line)
            
            # Don't forget the last paragraph
            if current_paragraph:
                paragraphs.append('<p>' + '<br>'.join(current_paragraph) + '</p>')
            
            formatted_content = '\n'.join(paragraphs)
            
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style>
        body {{ 
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        p {{ margin: 0 0 16px 0; padding: 0; }}
        .signature {{ 
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
        }}
        .quote {{
            margin: 20px 0;
            padding-left: 16px;
            border-left: 4px solid #ccc;
            color: #555;
        }}
    </style>
</head>
<body>
    <div>
        {formatted_content}
    </div>
</body>
</html>'''
            
            body = MIMEText(html_content, 'html', 'utf-8')
            
        message.attach(body)
        
        # Handle attachments from base64 data
        if data.get('attachments'):
            for attachment in data['attachments']:
                try:
                    # Check if attachment is a string or dictionary
                    if isinstance(attachment, str):
                        # Simple string attachment, skip it
                        logger.warning(f"Skipping attachment with string value: {attachment[:30]}...")
                        continue
                        
                    # Create attachment part
                    part = MIMEBase('application', 'octet-stream')
                    
                    # Set base64 payload
                    part.set_payload(base64.b64decode(attachment['content']))
                    
                    # Encode in ASCII to send as email
                    encoders.encode_base64(part)
                    
                    # Add header as key/value pair to attachment part
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}',
                    )
                    
                    # Add content type if provided
                    if attachment.get('mimeType'):
                        content_type = attachment['mimeType'].split('/')
                        if len(content_type) == 2:
                            part.replace_header('Content-Type', attachment['mimeType'])
                    
                    # Attach the part to the message
                    message.attach(part)
                    logger.info(f"Attached file: {attachment['filename']}")
                except Exception as attachment_error:
                    # Safely log the error without assuming attachment is a dictionary
                    filename = attachment.get('filename', 'unknown') if isinstance(attachment, dict) else 'unknown'
                    logger.error(f"Error attaching file {filename}: {str(attachment_error)}")
                    # Continue with other attachments even if this one fails
        
        # Convert to raw message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message, handling possible credential refresh
        try:
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Flag to track if email was sent even if database save failed
            email_sent = True
            db_save_success = False
            
            logger.info(f"Successfully sent email to {data['to']} via Gmail API")
        except Exception as api_error:
            # If we get a credential error, try to refresh and retry once
            logger.warning(f"Gmail API error (initial attempt): {str(api_error)}")
            
            # Get fresh credentials and rebuild service
            creds_data = request.session.get('gmail_credentials')
            if isinstance(creds_data, str):
                creds_data = json.loads(creds_data)
                
            try:
                credentials = Credentials(
                    token=creds_data['token'],
                    refresh_token=creds_data['refresh_token'],
                    token_uri=creds_data['token_uri'],
                    client_id=creds_data['client_id'],
                    client_secret=creds_data['client_secret'],
                    scopes=creds_data['scopes']
                )
                
                # Force refresh credentials
                credentials.refresh(Request())
                
                # Update session with refreshed credentials
                request.session['gmail_credentials'] = credentials.to_json()
                request.session.modified = True
                
                # Rebuild service with new credentials
                service = build('gmail', 'v1', credentials=credentials)
                
                # Retry sending with refreshed credentials
                sent_message = service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                # Flag to track if email was sent even if database save failed
                email_sent = True
                db_save_success = False
                
                logger.info("Email sent successfully after credentials refresh")
            except Exception as refresh_error:
                logger.error(f"Failed to refresh credentials and retry: {str(refresh_error)}")
                return JsonResponse({
                    'error': 'Gmail authentication expired',
                    'details': 'Authentication session expired. Please authenticate again.',
                    'redirect': '/gmail/authenticate/'
                }, status=HTTP_STATUS['unauthorized'])
        
        # Gracefully handle database save based on the actual schema
        db_save_success = False
        try:
            # Only try to save to database if email sending was successful
            if email_sent:
                # Use direct SQL with the correct schema
                with transaction.atomic():
                    cursor = connection.cursor()
                    
                    # Format recipients as a valid JSON array for PostgreSQL
                    if data.get('cc') or data.get('bcc'):
                        recipients_json = []
                        recipients_json.append({"email": data['to'], "type": "to"})
                        
                        if data.get('cc'):
                            for cc in data['cc'].split(','):
                                cc = cc.strip()
                                if cc:
                                    recipients_json.append({"email": cc, "type": "cc"})
                                    
                        if data.get('bcc'):
                            for bcc in data['bcc'].split(','):
                                bcc = bcc.strip()
                                if bcc:
                                    recipients_json.append({"email": bcc, "type": "bcc"})
                                    
                        # Convert to JSON string
                        recipients_data = json.dumps(recipients_json)
                    else:
                        # Simple case: just one recipient
                        recipients_data = json.dumps([{"email": data['to'], "type": "to"}])
                    
                    # Prepare snippet from body
                    snippet = data['body'][:150] + '...' if len(data['body']) > 150 else data['body']
                    
                    # Current timestamp
                    now = timezone.now().isoformat()
                    
                    # Execute SQL with the correct columns based on cursor rules
                    cursor.execute(
                        """
                        INSERT INTO emails (
                            id, user_email, subject, sender, recipients, date, 
                            snippet, has_attachments, folder, priority, 
                            category, last_modified
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            sent_message['id'],  # Use Gmail message ID as our ID
                            request.session.get('user_email', ''),
                            data['subject'],
                            request.session.get('user_email', ''),
                            recipients_data,  # Properly formatted JSON string
                            now,
                            snippet,
                            True if data.get('attachments') else False,  # has_attachments
                            'sent',
                            'medium',  # priority as string
                            'outbox',  # category as string
                            now  # last_modified
                        ]
                    )
                    
                    logger.info(f"Successfully saved email to database with direct SQL")
                    db_save_success = True
                
        except Exception as db_error:
            logger.error(f"Error saving sent email to database: {str(db_error)}", exc_info=True)
            db_save_success = False
            # Continue anyway - email was already sent
        
        # Create a more user-friendly response
        recipient_count = 1
        if data.get('cc'):
            recipient_count += len(data['cc'].split(','))
        if data.get('bcc'):
            recipient_count += len(data['bcc'].split(','))
            
        attachment_count = len(data.get('attachments', []))
        
        response_message = "Email sent successfully"
        if recipient_count > 1:
            response_message += f" to {recipient_count} recipients"
        if attachment_count > 0:
            response_message += f" with {attachment_count} attachment{'s' if attachment_count > 1 else ''}"
        
        # Add info about database save if relevant
        if not db_save_success:
            response_message += " (Note: Your email was sent, but couldn't be saved to your sent folder)"
            
        response_message += "!"
        
        return JsonResponse({
            'status': 'success',
            'message': response_message,
            'message_id': sent_message['id'],
            'timestamp': timezone.now().isoformat(),
            'recipient_count': recipient_count,
            'attachment_count': attachment_count,
            'db_save_success': db_save_success
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': 'Invalid JSON in request body'
        }, status=HTTP_STATUS['bad_request'])
    except GmailAPIError as e:
        logger.error(f"Gmail API error sending email: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['email_send_failed'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_gateway'])
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error'],
            'details': str(e)
        }, status=HTTP_STATUS['server_error']) 