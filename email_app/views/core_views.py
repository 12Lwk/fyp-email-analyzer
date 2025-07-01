from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction, connection
from django.conf import settings
from typing import Dict, Optional, Any, List, Union
import logging
import json
from datetime import datetime
import pytz
from dateutil import parser
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from django.contrib import messages
from django.core.management import call_command

from ..GMAIL_API.gmail_auth import GmailAuth
from ..GMAIL_API.gmail_api import GmailAPI
from ..utils.constants import (
    DB_CONFIG, ERROR_MESSAGES, HTTP_STATUS,
    MAX_RESULTS, DEFAULT_FOLDER, GMAIL_API_CONFIG,
    LOG_CONFIG
)
from ..ai_services.prioritazation.prioritization_service import EmailPrioritizationService
from ..ai_services import EmailCategorizationService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
gmail_auth: Optional[GmailAuth] = None
current_user_email: Optional[str] = None
priority_service = EmailPrioritizationService()
category_model = EmailCategorizationService()

def get_db_connection() -> psycopg2.extensions.connection:
    """Get a database connection with proper error handling.
    
    Returns:
        A PostgreSQL database connection
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise

def get_gmail_auth() -> GmailAuth:
    """Get or create a GmailAuth instance.
    
    Returns:
        A GmailAuth instance
        
    Raises:
        Exception: If GmailAuth creation fails
    """
    global gmail_auth
    try:
        if gmail_auth is None:
            gmail_auth = GmailAuth(
                credentials_path=GMAIL_API_CONFIG['credentials_path'],
                token_path=GMAIL_API_CONFIG['token_path'],
                scopes=GMAIL_API_CONFIG['scopes']
            )
        return gmail_auth
    except Exception as e:
        logger.error(f"Error creating GmailAuth instance: {str(e)}", exc_info=True)
        raise

@ensure_csrf_cookie
def serve_login(request: HttpRequest) -> HttpResponse:
    """Serve the login page.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Rendered login page
    """
    global gmail_auth, current_user_email
    gmail_auth = None
    current_user_email = None
    return render(request, 'email_app/login.html')

def parse_and_normalize_date(raw_date: Union[str, datetime, pd.Timestamp]) -> Optional[str]:
    """Parse and normalize date to UTC format.
    
    Args:
        raw_date: The date to parse in various formats
        
    Returns:
        Normalized UTC date string or None if parsing fails
    """
    try:
        if raw_date is None:
            return None
            
        if isinstance(raw_date, pd.Timestamp):
            parsed_date = raw_date.to_pydatetime()
        elif isinstance(raw_date, datetime):
            parsed_date = raw_date
        else:
            parsed_date = parser.parse(str(raw_date))
        
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=pytz.UTC)
        else:
            parsed_date = parsed_date.astimezone(pytz.UTC)
        
        return parsed_date.strftime('%Y-%m-%d %H:%M:%S%z')
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing date: {str(e)}", exc_info=True)
        logger.debug(f"Raw date type: {type(raw_date)}")
        logger.debug(f"Raw date value: {raw_date}")
        return None

@transaction.atomic
def save_email_to_db(email_data: Dict[str, Any], user_email: str) -> bool:
    """Save email data to database with transaction management.
    
    Args:
        email_data: Dictionary containing email data
        user_email: Email address of the user
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        # Get priority prediction
        priority_pred, priority_scores, priority_explanation = priority_service.predict_priority(
            subject=email_data['subject'],
            body=email_data.get('snippet', ''),
            sender=email_data['sender']
        )
        
        # Get category prediction using the new service
        # Prepare data for categorization
        categorization_input = {
            'subject': email_data.get('subject', ''),
            'content': email_data.get('snippet', ''), # Assuming snippet is sufficient, or use full body if available
            'sender': email_data.get('sender', ''),
            'recipients': email_data.get('recipients', []) # Pass the recipients list
        }
        category_result = category_model.categorize_email(categorization_input)
        
        # Parse date
        formatted_date = parse_and_normalize_date(email_data['date'])
        if formatted_date is None:
            logger.warning("Skipping email due to date parsing error.")
            return False

        # Store in database using psycopg2 for better error handling
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO emails (
                        id, user_email, subject, sender, recipients, date,
                        snippet, has_attachments, attachments, star, label,
                        folder, last_modified, priority, priority_score,
                        priority_explanation, priority_last_updated,
                        category, category_confidence, category_last_updated
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id, user_email) DO UPDATE SET
                        last_modified = EXCLUDED.last_modified,
                        priority = EXCLUDED.priority,
                        priority_score = EXCLUDED.priority_score,
                        priority_explanation = EXCLUDED.priority_explanation,
                        priority_last_updated = EXCLUDED.priority_last_updated,
                        category = EXCLUDED.category,
                        category_confidence = EXCLUDED.category_confidence,
                        category_last_updated = EXCLUDED.category_last_updated
                """, [
                    email_data['id'], user_email, email_data['subject'],
                    email_data['sender'], json.dumps([{"email": email.strip()} for email in email_data.get('recipients', '').split(',') if email.strip()]),
                    formatted_date, email_data.get('snippet', ''),
                    email_data.get('has_attachments', False),
                    json.dumps(email_data.get('attachments', [])),
                    email_data.get('star', False),
                    email_data.get('label', ''),
                    email_data.get('folder', DEFAULT_FOLDER),
                    datetime.now(pytz.UTC),
                    priority_pred,
                    priority_scores.get(priority_pred, 0.0),
                    priority_explanation,
                    datetime.now(pytz.UTC),
                    category_result['category'],
                    category_result.get('confidence', 0.0),
                    datetime.now(pytz.UTC)
                ])
                conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return False
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error saving email to database: {str(e)}", exc_info=True)
        return False

def check_gmail_auth(request):
    """Check if user is authenticated with Gmail."""
    try:
        # Check session
        if not request.session.session_key:
            return JsonResponse({
                'status': 'error',
                'message': 'No active session'
            }, status=401)
            
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated with Gmail'
            }, status=401)
            
        # Check user email
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Update last activity
        request.session['last_activity'] = datetime.now(pytz.UTC).isoformat()
        request.session.save()
        
        return JsonResponse({
            'status': 'success',
            'is_gmail_authenticated': True,
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Error checking Gmail auth: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Error checking authentication'
        }, status=500)

def inbox_email(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Display inbox emails."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return redirect('email_app:login')
            
        user_email = request.session.get('user_email')
        if not user_email:
            return redirect('email_app:login')
            
        with connection.cursor() as cursor:
            # Get emails
            cursor.execute("""
                SELECT id, subject, sender, date, priority, category, snippet
                FROM emails 
                WHERE user_email = %s AND folder = 'inbox'
                ORDER BY date DESC
            """, [user_email])
            
            emails = []
            for row in cursor.fetchall():
                emails.append(dict(zip(['id', 'subject', 'sender', 'date', 'priority', 'category', 'snippet'], row)))
            
            return render(request, 'email_app/inbox_email.html', {
                'emails': emails,
                'user_email': user_email
            })
            
    except Exception as e:
        logger.error(f"Error loading inbox: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to load inbox'}, status=500)

def sent_email(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Display sent emails."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return redirect('email_app:login')
            
        user_email = request.session.get('user_email')
        if not user_email:
            return redirect('email_app:login')
            
        with connection.cursor() as cursor:
            # Get emails
            cursor.execute("""
                SELECT id, subject, recipients, date, priority, category, snippet
                FROM emails 
                WHERE user_email = %s AND UPPER(folder) = 'SENT'
                ORDER BY date DESC
            """, [user_email])
            
            columns = ['id', 'subject', 'recipients', 'date', 'priority', 'category', 'snippet']
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for display
            for email in emails:
                if email.get('date'):
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
            
            return render(request, 'email_app/sent_email.html', {
                'emails': emails,
                'user_email': user_email,
                'folder': 'Sent'
            })
            
    except Exception as e:
        logger.error(f"Error loading sent emails: {str(e)}", exc_info=True)
        return render(request, 'email_app/sent_email.html', {
            'error': f"Error: {str(e)} ({type(e).__name__})",
            'folder': 'Sent'
        })

def spam_email(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Display spam emails."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return redirect('email_app:login')
            
        user_email = request.session.get('user_email')
        if not user_email:
            return redirect('email_app:login')
            
        with connection.cursor() as cursor:
            # Get emails
            cursor.execute("""
                SELECT id, subject, sender, date, priority, category
                FROM emails 
                WHERE user_email = %s AND folder = 'spam'
                ORDER BY date DESC
            """, [user_email])
            
            emails = []
            for row in cursor.fetchall():
                emails.append(dict(zip(['id', 'subject', 'sender', 'date', 'priority', 'category'], row)))
            
            return render(request, 'email_app/spam_email.html', {
                'emails': emails,
                'user_email': user_email
            })
            
    except Exception as e:
        logger.error(f"Error loading spam emails: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to load spam emails'}, status=500)

def spam_email_detail(request: HttpRequest, email_id: str) -> Union[HttpResponse, JsonResponse]:
    """View for displaying spam email details."""
    logger.info(f"Accessing spam email detail for ID: {email_id}")
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            return redirect('email_app:login')
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            return redirect('email_app:login')
        if not email_id or not email_id.strip():
            logger.error("Invalid email ID provided")
            return redirect('email_app:spam_email')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, user_email, subject, sender, recipients, 
                    date, snippet, has_attachments, attachments,
                    star, label, folder, last_modified, 
                    priority, priority_score, priority_explanation, priority_last_updated,
                    category, category_confidence, category_last_updated
                FROM emails 
                WHERE id = %s AND user_email = %s AND category = 'Spam Email'
            """, [email_id, user_email])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if not row:
                logger.error(f"Spam email with ID {email_id} not found for user {user_email} in category 'Spam Email'")
                return render(request, 'email_app/spam_email_detail.html', {
                    'error': f"Spam email not found or you do not have access.",
                    'user_email': user_email,
                    'email': None,
                    'folder': 'SPAM'
                })
            email_data = dict(zip(columns, row))
            # Format dates for display
            if email_data.get('date'):
                email_data['date'] = email_data['date'].strftime('%Y-%m-%d %H:%M:%S')
            if email_data.get('last_modified'):
                email_data['last_modified'] = email_data['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
            if email_data.get('priority_last_updated'):
                email_data['priority_last_updated'] = email_data['priority_last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            if email_data.get('category_last_updated'):
                email_data['category_last_updated'] = email_data['category_last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            return render(request, 'email_app/spam_email_detail.html', {
                'email': email_data,
                'user_email': user_email,
                'folder': 'SPAM',
                'error': None
            })
    except Exception as e:
        logger.error(f"Error accessing spam email detail: {str(e)}", exc_info=True)
        return render(request, 'email_app/spam_email_detail.html', {
            'error': f"Error accessing spam email detail: {str(e)}",
            'user_email': request.session.get('user_email', ''),
            'email': None,
            'folder': 'SPAM'
        })

def settings_view(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Display settings page."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return redirect('email_app:login')
            
        user_email = request.session.get('user_email')
        if not user_email:
            return redirect('email_app:login')
            
        return render(request, 'email_app/settings.html', {
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to load settings'}, status=500)

@csrf_exempt
@require_POST
def upload_excel(request):
    """Handle Excel file upload."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
            
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Handle file upload
        if 'file' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'No file uploaded'
            }, status=400)
            
        file = request.FILES['file']
        if not file.name.endswith('.xlsx'):
            return JsonResponse({
                'status': 'error',
                'message': 'Only Excel files are allowed'
            }, status=400)
            
        # Process file
        df = pd.read_excel(file)
        
        # Save to database
        with connection.cursor() as cursor:
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO emails (
                        id, user_email, subject, sender, recipients, date,
                        snippet, has_attachments, attachments, star, label,
                        folder, last_modified, priority, priority_score,
                        priority_explanation, priority_last_updated,
                        category, category_confidence, category_last_updated
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id, user_email) DO UPDATE SET
                        last_modified = EXCLUDED.last_modified,
                        priority = EXCLUDED.priority,
                        priority_score = EXCLUDED.priority_score,
                        priority_explanation = EXCLUDED.priority_explanation,
                        priority_last_updated = EXCLUDED.priority_last_updated,
                        category = EXCLUDED.category,
                        category_confidence = EXCLUDED.category_confidence,
                        category_last_updated = EXCLUDED.category_last_updated
                """, [
                    row['id'], user_email, row['subject'],
                    row['sender'], json.dumps([{"email": email.strip()} for email in row.get('recipients', '').split(',') if email.strip()]),
                    row['date'], row.get('snippet', ''),
                    row.get('has_attachments', False),
                    json.dumps(row.get('attachments', [])),
                    row.get('star', False),
                    row.get('label', ''),
                    row.get('folder', DEFAULT_FOLDER),
                    datetime.now(pytz.UTC),
                    row.get('priority', 'Low'),
                    row.get('priority_score', 0.0),
                    row.get('priority_explanation', ''),
                    datetime.now(pytz.UTC),
                    row.get('category', 'Uncategorized'),
                    row.get('category_confidence', 0.0),
                    datetime.now(pytz.UTC)
                ])
                
        return JsonResponse({
            'status': 'success',
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to upload file'
        }, status=500)

@require_http_methods(["GET"])
def initialize_email_sync(request: HttpRequest) -> JsonResponse:
    """Initialize email sync."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
            
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Initialize sync
        call_command('sync_emails', user_email=user_email)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Email sync initialized'
        })
        
    except Exception as e:
        logger.error(f"Error initializing sync: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to initialize sync'
        }, status=500)

@require_http_methods(["GET"])
def check_sync_status(request: HttpRequest) -> JsonResponse:
    """Check email sync status."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
            
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Check sync status
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total_emails
                FROM emails 
                WHERE user_email = %s
            """, [user_email])
            
            result = cursor.fetchone()
            total_emails = result[0] if result else 0
            
        return JsonResponse({
            'status': 'success',
            'total_emails': total_emails
        })
        
    except Exception as e:
        logger.error(f"Error checking sync status: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to check sync status'
        }, status=500)

def compose(request: HttpRequest) -> JsonResponse:
    """Handle email composition."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
            
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Handle email composition
        if request.method == 'POST':
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('recipients'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Recipients are required'
                }, status=400)
                
            if not data.get('subject'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Subject is required'
                }, status=400)
                
            if not data.get('body'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Body is required'
                }, status=400)
                
            # Send email
            gmail = get_gmail_auth()
            gmail.send_email(
                to=data['recipients'],
                subject=data['subject'],
                body=data['body']
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Email sent successfully'
            })
            
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)
        
    except Exception as e:
        logger.error(f"Error composing email: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to compose email'
        }, status=500)

@ensure_csrf_cookie
def view_emails(request: HttpRequest) -> JsonResponse:
    """View emails."""
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
            
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No user email in session'
            }, status=401)
            
        # Get folder filter if provided
        folder = request.GET.get('folder')
        base_query = """
            SELECT id, subject, sender, recipients, date, priority, category, snippet, folder
            FROM emails 
            WHERE user_email = %s
        """
        params = [user_email]
        
        # Add folder filter if provided
        if folder:
            base_query += " AND UPPER(folder) = UPPER(%s)"
            params.append(folder)
            
        # Add ordering
        base_query += " ORDER BY date DESC"
        
        # Get emails
        with connection.cursor() as cursor:
            cursor.execute(base_query, params)
            
            columns = [col[0] for col in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for display
            for email in emails:
                if email.get('date'):
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
            
        return JsonResponse({
            'status': 'success',
            'emails': emails
        })
        
    except Exception as e:
        logger.error(f"Error viewing emails: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to view emails'
        }, status=500) 