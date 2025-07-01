from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db import connection
from typing import Dict, Any, Union, Optional, List
import logging
import json
import os
from dotenv import load_dotenv
import psycopg2
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import uuid
import datetime
import pytz
from django.views.decorators.csrf import csrf_exempt

from ..utils.constants import ERROR_MESSAGES, HTTP_STATUS
from ..ai_services.summarization.summarization_service import SummarizationService
from ..ai_services.recommendations.recommendation_service import RecommendationService
from ..ai_services.llm.llm_service import LLMService
from ..GMAIL_API.gmail_auth import check_gmail_auth

logger = logging.getLogger(__name__)

EmailData = Dict[str, Any]

# Try to load environment variables with different encodings
try:
    load_dotenv(encoding='utf-8')
except UnicodeDecodeError:
    try:
        load_dotenv(encoding='utf-16')
    except Exception as e:
        logger.warning(f"Could not load .env file: {str(e)}")
        # Continue without .env file - we'll use default values

def get_db_connection():
    """Establish a connection to the PostgreSQL database using environment variables."""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'email_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'email1234'),  # Added default password
            port=os.getenv('DB_PORT', '5432')
        )
        return connection
    except psycopg2.Error as e:
        logging.error(f"Database connection error: {str(e)}")
        raise

def inbox_email(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """View for displaying the email inbox."""
    logger.info(f"Accessing inbox")
    logger.info(f"Session data: {dict(request.session)}")
    
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            messages.error(request, ERROR_MESSAGES['GMAIL_AUTH_REQUIRED'])
            return redirect('email_app:login')
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            messages.error(request, ERROR_MESSAGES['AUTH_REQUIRED'])
            return redirect('email_app:login')

        with connection.cursor() as cursor:
            # First check if any emails exist for this user
            check_query = "SELECT COUNT(*) FROM emails WHERE user_email = %s"
            cursor.execute(check_query, [user_email])
            total_emails = cursor.fetchone()[0]
            logger.info(f"Total emails found for user: {total_emails}")
            
            # Get inbox emails
            query = """
                SELECT 
                    id, 
                    CASE WHEN subject IS NULL OR subject = '' THEN 'No Subject' ELSE subject END as subject,
                    sender, date, snippet,
                    has_attachments, star, priority, category,
                    label, folder, priority_score, category_confidence
                FROM emails 
                WHERE user_email = %s AND folder = 'INBOX'
                ORDER BY date DESC
            """
            
            cursor.execute(query, [user_email])
            
            columns = [col[0] for col in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for display
            for email in emails:
                if email['date']:
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
                # Ensure subject is never empty (belt and suspenders approach)
                if not email.get('subject') or email['subject'] == '':
                    email['subject'] = 'No Subject'
            
            context = {
                'emails': emails,
                'folder': 'Inbox',
                'user_email': user_email,
                'total_emails': total_emails
            }
            
            return render(request, 'email_app/inbox_email.html', context)
            
    except Exception as e:
        logger.error(f"Error accessing inbox: {str(e)}", exc_info=True)
        error_msg = f"Error: {str(e)} ({type(e).__name__})"
        logger.error(error_msg)
        return render(request, 'email_app/inbox_email.html', {
            'error': error_msg,
            'folder': 'Inbox'
        })

def redirect_old_detail(request: HttpRequest, email_id: str) -> HttpResponse:
    """Redirect old email detail URLs to the new format."""
    logger.info(f"Redirecting old URL format for email ID: {email_id}")
    
    # Check Gmail authentication
    if not request.session.get('is_gmail_authenticated'):
        logger.warning("User not authenticated with Gmail")
        messages.error(request, ERROR_MESSAGES['GMAIL_AUTH_REQUIRED'])
        request.session['next'] = request.path
        return redirect('email_app:login')
    
    return redirect('email_app:inbox_email_detail', email_id=email_id)

def inbox_email_detail(request: HttpRequest, email_id: str) -> Union[HttpResponse, JsonResponse]:
    """View for displaying email details."""
    logger.info(f"Accessing email detail for ID: {email_id}")
    logger.info(f"Session ID: {request.session.session_key}")
    logger.info(f"Session data: {dict(request.session)}")
    logger.info(f"Gmail authenticated: {request.session.get('is_gmail_authenticated')}")
    
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            messages.error(request, ERROR_MESSAGES['GMAIL_AUTH_REQUIRED'])
            request.session['next'] = request.path
            return redirect('email_app:login')
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            messages.error(request, ERROR_MESSAGES['AUTH_REQUIRED'])
            return redirect('email_app:login')
        
        # Validate email_id
        if not email_id or not email_id.strip():
            logger.error("Invalid email ID provided")
            messages.error(request, 'Invalid email ID')
            return redirect('email_app:inbox_email')
        
        with connection.cursor() as cursor:
            # Get full email details using only existing columns
            cursor.execute("""
                SELECT 
                    id, user_email, subject, sender, recipients, 
                    date, snippet, has_attachments, attachments,
                    star, label, folder, last_modified, 
                    priority, priority_score, priority_explanation, priority_last_updated,
                    category, category_confidence, category_last_updated
                FROM emails 
                WHERE id = %s AND user_email = %s
            """, [email_id, user_email])
            
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Email '{email_id}' not found")
                messages.error(request, 'Email not found')
                return redirect('email_app:inbox_email')
                
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
            
            # Store email data in session to maintain state
            request.session['current_email'] = email_data
            request.session.modified = True
            
            # Log successful access
            logger.info(f"Successfully retrieved email {email_id} for user {user_email}")
            
            all_categories = [
                "Work or Business Email",
                "Finance & Transaction Email",
                "Personal Email", 
                "Meeting & Schedule Email",
                "Legal & Contractual Email",
                "Spam Email",
                "IT Alerts & System Notifications Email",
                "Internal Policies & HR Updates Email",
                "Social Media Email",
                "Promotions or Marketing Email",
                "Utilities Bill Email"
            ]
            all_priorities = ["high", "medium", "low"]
            return render(request, 'email_app/inbox_email_detail.html', {
                'email': email_data,
                'user_email': user_email,
                'folder': email_data.get('folder', 'INBOX'),
                'all_categories': all_categories,
                'all_priorities': all_priorities,
            })
            
    except Exception as e:
        logger.error(f"Error accessing email detail: {str(e)}", exc_info=True)
        messages.error(request, f'Error loading email: {str(e)}')
        return redirect('email_app:inbox_email')

def sent_email_detail(request: HttpRequest, email_id: str) -> Union[HttpResponse, JsonResponse]:
    """View for displaying sent email details."""
    logger.info(f"Accessing sent email detail for ID: {email_id}")
    logger.info(f"Session ID: {request.session.session_key}")
    logger.info(f"Session data: {dict(request.session)}")
    logger.info(f"Gmail authenticated: {request.session.get('is_gmail_authenticated')}")
    
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            messages.error(request, ERROR_MESSAGES['GMAIL_AUTH_REQUIRED'])
            request.session['next'] = request.path
            return redirect('email_app:login')
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            messages.error(request, ERROR_MESSAGES['AUTH_REQUIRED'])
            return redirect('email_app:login')
        
        # Validate email_id
        if not email_id or not email_id.strip():
            logger.error("Invalid email ID provided")
            messages.error(request, 'Invalid email ID')
            return redirect('email_app:sent_email')
        
        with connection.cursor() as cursor:
            # Get full email details using only existing columns
            cursor.execute("""
                SELECT 
                    id, user_email, subject, sender, recipients, 
                    date, snippet, has_attachments, attachments,
                    star, label, folder, last_modified, 
                    priority, priority_score, priority_explanation, priority_last_updated,
                    category, category_confidence, category_last_updated
                FROM emails 
                WHERE id = %s AND user_email = %s AND folder ILIKE 'sent'
            """, [email_id, user_email])
            
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Sent email '{email_id}' not found")
                messages.error(request, 'Email not found')
                return redirect('email_app:sent_email')
                
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
            
            # Store email data in session to maintain state
            request.session['current_email'] = email_data
            request.session.modified = True
            
            # Log successful access
            logger.info(f"Successfully retrieved sent email {email_id} for user {user_email}")
            
            return render(request, 'email_app/sent_email_detail.html', {
                'email': email_data,
                'user_email': user_email,
                'folder': 'SENT'
            })
            
    except Exception as e:
        logger.error(f"Error accessing sent email detail: {str(e)}", exc_info=True)
        messages.error(request, f'Error loading email: {str(e)}')
        return redirect('email_app:sent_email')

@ensure_csrf_cookie
@require_http_methods(["GET"])
def view_emails(request: HttpRequest) -> JsonResponse:
    """API endpoint to view emails with optional filtering."""
    logger.info("=" * 80)
    logger.info("view_emails endpoint called")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request GET params: {request.GET}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request user: {request.user}")
    logger.info(f"Request session: {dict(request.session)}")
    logger.info("=" * 80)
    
    try:
        # Get user email from request.user or session
        user_email = request.user.email if hasattr(request.user, 'email') else request.session.get('user_email')
        
        # Debug logging
        logger.info(f"Debug - User email: {user_email}")

        if not user_email:
            logger.warning("No user email found")
            return JsonResponse({
                'status': 'error',
                'message': 'Please log in again.'
            }, status=401)

        # Get query parameters with defaults
        folder = request.GET.get('folder', 'INBOX').upper()
        logger.info(f"Debug - Using folder filter: {folder}")
        
        try:
            page = max(1, int(request.GET.get('page', 1)))
            per_page = min(50, max(1, int(request.GET.get('per_page', 10))))
        except ValueError:
            page = 1
            per_page = 10
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build the base query
        query = """
            SELECT 
                id, subject, sender, recipients, date, snippet,
                has_attachments, star, priority, category,
                label, folder
            FROM emails 
            WHERE user_email = %s AND UPPER(folder) = %s
        """
        params = [user_email, folder]

        # Add category filter if provided - modified to support multiple categories
        category_param = request.GET.get('category')
        if category_param and category_param != 'all':
            # Split the category parameter by comma and create an IN clause
            categories = [cat.strip() for cat in category_param.split(',') if cat.strip()]
            logger.info(f"Debug - Multiple categories filter: {categories}")
            
            if categories:
                placeholders = ', '.join(['%s'] * len(categories))
                query += f" AND category IN ({placeholders})"
                params.extend(categories)

        # Add priority filter if provided
        priority_param = request.GET.get('priority')
        if priority_param and priority_param != 'all':
            # Check if multiple priorities are provided (comma-separated)
            priorities = [p.strip().upper() for p in priority_param.split(',') if p.strip()]
            logger.info(f"Debug - Priority filter: {priorities}")
            
            if priorities:
                if len(priorities) == 1:
                    query += " AND UPPER(priority) = %s"
                    params.append(priorities[0])
                else:
                    # Handle multiple priorities with IN clause
                    placeholders = ', '.join(['%s'] * len(priorities))
                    query += f" AND UPPER(priority) IN ({placeholders})"
                    params.extend(priorities)

        # Add search filter if provided
        search = request.GET.get('search')
        if search:
            query += " AND (subject ILIKE %s OR sender ILIKE %s OR snippet ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        # Add ordering and pagination
        query += " ORDER BY date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Debug logging
        logger.info(f"Debug - SQL Query: {query}")
        logger.info(f"Debug - Query params: {params}")
        
        with connection.cursor() as cursor:
            # First check if any emails exist for this user
            check_query = "SELECT COUNT(*) FROM emails WHERE user_email = %s AND UPPER(folder) = %s"
            cursor.execute(check_query, [user_email, folder])
            total_emails = cursor.fetchone()[0]
            logger.info(f"Debug - Total emails found for user: {total_emails}")
            
            if total_emails == 0:
                return JsonResponse({
                    'status': 'success',
                    'data': {
                        'emails': [],
                        'pagination': {
                            'current_page': page,
                            'per_page': per_page,
                            'total_items': 0,
                            'total_pages': 0
                        }
                    }
                })
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            columns = [col[0] for col in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for JSON and ensure all values are JSON serializable
            for email in emails:
                if email['date']:
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
                # Convert any non-serializable values to strings
                for key, value in email.items():
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        email[key] = str(value)
            
            response_data = {
                'status': 'success',
                'data': {
                    'emails': emails,
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'total_items': total_emails,
                        'total_pages': (total_emails + per_page - 1) // per_page
                    }
                }
            }
            
            # Debug logging
            logger.info(f"Debug - Response data structure: {list(response_data.keys())}")
            logger.info(f"Debug - Found {len(emails)} emails for folder {folder}")
            
            return JsonResponse(response_data)
            
    except Exception as e:
        logger.error(f"Error retrieving emails: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_email_detail(request: HttpRequest, email_id: str) -> JsonResponse:
    """Get details for a specific email."""
    logger.info(f"API request for email detail: {email_id}")
    
    try:
        # Check Gmail authentication
        if not check_gmail_auth(request):
            logger.warning("User not authenticated with Gmail")
            return JsonResponse({
                'error': ERROR_MESSAGES['GMAIL_AUTH_REQUIRED'],
                'redirect': '/gmail/auth/'
            }, status=HTTP_STATUS['unauthorized'])
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            return JsonResponse({'error': ERROR_MESSAGES['AUTH_REQUIRED']}, status=HTTP_STATUS['unauthorized'])
        
        # Validate email_id
        if not email_id or not email_id.strip():
            logger.error("Invalid email ID provided")
            return JsonResponse({'error': 'Invalid email ID'}, status=HTTP_STATUS['bad_request'])
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get full email details
                cur.execute("""
                    SELECT 
                        id, user_email, subject, sender, recipients, 
                        date, snippet, has_attachments, attachments,
                        star, label, folder, last_modified, 
                        priority, priority_score, priority_explanation, priority_last_updated,
                        category, category_confidence, category_last_updated,
                        CASE WHEN subject IS NULL OR subject = '' THEN 'No Subject' ELSE subject END as display_subject
                    FROM emails 
                    WHERE id = %s AND user_email = %s
                """, [email_id, user_email])
                
                columns = [col[0] for col in cur.description]
                row = cur.fetchone()
                
                if not row:
                    logger.error(f"Email '{email_id}' not found")
                    return JsonResponse({'error': 'Email not found'}, status=HTTP_STATUS['not_found'])
                    
                email_data = dict(zip(columns, row))
                
                # Make sure subject is never null or empty
                if email_data.get('subject') is None or email_data.get('subject') == '':
                    email_data['subject'] = 'No Subject'
                
                # Handle sender field for display
                if 'sender' in email_data and email_data['sender']:
                    # Try to extract name and email parts
                    sender_parts = email_data['sender'].split('<')
                    if len(sender_parts) > 1:
                        email_data['sender_name'] = sender_parts[0].strip()
                        email_data['sender_email'] = sender_parts[1].rstrip('>')
                    else:
                        email_data['sender_name'] = email_data['sender']
                        email_data['sender_email'] = email_data['sender']
                
                # Format dates for JSON serialization
                for date_field in ['date', 'last_modified', 'priority_last_updated', 'category_last_updated']:
                    if email_data.get(date_field):
                        email_data[date_field] = email_data[date_field].isoformat()
                
                # Parse JSON fields
                if email_data.get('attachments') and isinstance(email_data['attachments'], str):
                    try:
                        email_data['attachments'] = json.loads(email_data['attachments'])
                    except json.JSONDecodeError:
                        email_data['attachments'] = []
                
                if email_data.get('recipients') and isinstance(email_data['recipients'], str):
                    try:
                        email_data['recipients'] = json.loads(email_data['recipients'])
                    except json.JSONDecodeError:
                        email_data['recipients'] = [email_data['recipients']]
                
                # Log successful access
                logger.info(f"Successfully retrieved email {email_id} for user {user_email}")
                
                return JsonResponse(email_data)
                
    except Exception as e:
        logger.error(f"Error retrieving email details: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f"Failed to retrieve email: {str(e)}"
        }, status=HTTP_STATUS['server_error'])

def delete_email(request: HttpRequest, email_id: str) -> JsonResponse:
    """Delete an email from the database.
    
    Args:
        request: The HTTP request object
        email_id: The unique identifier of the email to delete
        
    Returns:
        JsonResponse with success/error message
    """
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['GMAIL_AUTH_REQUIRED']
            }, status=401)
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['AUTH_REQUIRED']
            }, status=401)
            
        if not email_id:
            logger.error("Email ID not provided")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['invalid_request']
            }, status=400)
        
        with connection.cursor() as cursor:
            # Check if email exists and belongs to user
            cursor.execute("""
                SELECT id FROM emails 
                WHERE id = %s AND user_email = %s
            """, [email_id, user_email])
            
            if not cursor.fetchone():
                logger.warning(f"Email '{email_id}' not found for user {user_email}")
                return JsonResponse({
                    'status': 'error',
                    'message': ERROR_MESSAGES['not_found']
                }, status=404)
            
            # Delete the email
            cursor.execute("""
                DELETE FROM emails 
                WHERE id = %s AND user_email = %s
            """, [email_id, user_email])
            
            connection.commit()
            
            logger.info(f"Successfully deleted email '{email_id}'")
            return JsonResponse({
                'status': 'success',
                'message': 'Email deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': ERROR_MESSAGES['processing_error']
        }, status=500)

def mark_as_read(request: HttpRequest, email_id: str) -> JsonResponse:
    """Mark an email as read in the database.
    
    Args:
        request: The HTTP request object
        email_id: The unique identifier of the email to mark as read
        
    Returns:
        JsonResponse with success/error message
    """
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['GMAIL_AUTH_REQUIRED']
            }, status=401)
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['AUTH_REQUIRED']
            }, status=401)
            
        if not email_id:
            logger.error("Email ID not provided")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['invalid_request']
            }, status=400)
        
        with connection.cursor() as cursor:
            # Check if email exists and belongs to user
            cursor.execute("""
                SELECT id FROM emails 
                WHERE id = %s AND user_email = %s
            """, [email_id, user_email])
            
            if not cursor.fetchone():
                logger.warning(f"Email '{email_id}' not found for user {user_email}")
                return JsonResponse({
                    'status': 'error',
                    'message': ERROR_MESSAGES['not_found']
                }, status=404)
            
            # Mark email as read
            cursor.execute("""
                UPDATE emails 
                SET is_read = true,
                    last_modified = NOW()
                WHERE id = %s AND user_email = %s
            """, [email_id, user_email])
            
            connection.commit()
            
            logger.info(f"Successfully marked email '{email_id}' as read")
            return JsonResponse({
                'status': 'success',
                'message': 'Email marked as read'
            })
            
    except Exception as e:
        logger.error(f"Error marking email as read: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': ERROR_MESSAGES['processing_error']
        }, status=500)

def get_sent_emails(request: HttpRequest) -> JsonResponse:
    """API endpoint to get sent emails.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse containing sent emails or error message
    """
    logger.info("Getting sent emails")
    
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['GMAIL_AUTH_REQUIRED']
            }, status=401)
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['AUTH_REQUIRED']
            }, status=401)
        
        with connection.cursor() as cursor:
            # Get sent emails
            cursor.execute("""
                SELECT id, subject, recipients, date, priority, category, snippet
                FROM emails 
                WHERE user_email = %s AND UPPER(folder) = 'SENT'
                ORDER BY date DESC
            """, [user_email])
            
            columns = [col[0] for col in cursor.description]
            sent_emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for JSON
            for email in sent_emails:
                if email.get('date'):
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return JsonResponse({
                'status': 'success',
                'data': {
                    'sent_emails': sent_emails
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting sent emails: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_spam_emails(request: HttpRequest) -> JsonResponse:
    """API endpoint for retrieving spam emails based on category."""
    logger.info("Accessing spam emails API (filtering by category)")
    
    try:
        # Check Gmail authentication
        if not request.session.get('is_gmail_authenticated'):
            logger.warning("User not authenticated with Gmail")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['GMAIL_AUTH_REQUIRED']
            }, status=HTTP_STATUS['unauthorized'])
        
        # Get user email from session
        user_email = request.session.get('user_email')
        if not user_email:
            logger.warning("No user email found in session")
            return JsonResponse({
                'status': 'error',
                'message': ERROR_MESSAGES['AUTH_REQUIRED']
            }, status=HTTP_STATUS['unauthorized'])
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        search_query = request.GET.get('search', '').strip()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        with connection.cursor() as cursor:
            # Base query for spam emails, filtering by category
            base_query = """
                SELECT 
                    id, 
                    CASE WHEN subject IS NULL OR subject = '' THEN 'No Subject' ELSE subject END as subject,
                    sender, date, snippet,
                    has_attachments, star, priority, category,
                    label, folder, priority_score, category_confidence
                FROM emails 
                WHERE user_email = %s AND category = 'Spam Email'
            """
            
            # Add search condition if search query exists
            if search_query:
                base_query += """
                    AND (
                        LOWER(subject) LIKE LOWER(%s) OR
                        LOWER(sender) LIKE LOWER(%s) OR
                        LOWER(snippet) LIKE LOWER(%s)
                    )
                """
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_query"
            if search_query:
                cursor.execute(count_query, [user_email, f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
            else:
                cursor.execute(count_query, [user_email])
            total_count = cursor.fetchone()[0]
            
            # Add pagination
            base_query += " ORDER BY date DESC LIMIT %s OFFSET %s"
            
            # Execute main query
            if search_query:
                cursor.execute(base_query, [
                    user_email, 
                    f'%{search_query}%', 
                    f'%{search_query}%', 
                    f'%{search_query}%',
                    page_size, 
                    offset
                ])
            else:
                cursor.execute(base_query, [user_email, page_size, offset])
            
            columns = [col[0] for col in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates for display
            for email in emails:
                if email['date']:
                    email['date'] = email['date'].strftime('%Y-%m-%d %H:%M:%S')
                # Ensure subject is never empty
                if not email.get('subject') or email['subject'] == '':
                    email['subject'] = 'No Subject'
            
            return JsonResponse({
                'status': 'success',
                'emails': emails,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })
            
    except Exception as e:
        logger.error(f"Error accessing spam emails: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error loading spam emails: {str(e)}'
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
def correct_email_label(request: HttpRequest) -> JsonResponse:
    print("correct_email_label view called with method:", request.method)
    try:
        data = json.loads(request.body)
        email_id = data.get('email_id')
        new_category = data.get('category')
        new_priority = data.get('priority')
        if not email_id or not new_category or not new_priority:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields.'}, status=400)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE emails SET category=%s, priority=%s, category_last_updated=NOW(), priority_last_updated=NOW() WHERE id=%s
                """,
                [new_category, new_priority, email_id]
            )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error correcting email label: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)