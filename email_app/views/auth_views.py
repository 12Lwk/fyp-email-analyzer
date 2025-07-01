from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from typing import Union, Optional, TypedDict, Dict, Any, cast, Literal
import logging
import json
from django.utils import timezone

from ..utils.constants import ERROR_MESSAGES, HTTP_STATUS

logger = logging.getLogger(__name__)

class AuthResponse(TypedDict):
    """Type definition for authentication response."""
    status: Literal['success', 'error']
    message: str
    details: Optional[str]

@require_http_methods(["GET"])
def serve_login(request: HttpRequest) -> HttpResponse:
    """Serve the login page."""
    logger.info("Serving login page")
    logger.info(f"Session ID: {request.session.session_key}")
    logger.info(f"Session data: {dict(request.session)}")
    
    # If user is already authenticated, redirect to next URL or dashboard
    if request.session.get('is_gmail_authenticated'):
        next_url = request.session.get('next') or reverse('email_app:email_dashboard')
        # Clear the next URL from session after using it
        request.session.pop('next', None)
        return redirect(next_url)
    
    # Store next URL in session if provided in query params
    next_url = request.GET.get('next')
    if next_url:
        request.session['next'] = next_url
        request.session.modified = True
    
    return render(request, 'email_app/login.html')

@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Handle user login."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email and password are required'
                }, status=400)
            
            # Clear any existing session data
            request.session.flush()
            
            # Set session data
            request.session['is_gmail_authenticated'] = True
            request.session['user_email'] = email
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Set session expiry to 7 days for better persistence
            request.session.set_expiry(604800)  # 7 days in seconds
            
            # Force session save
            request.session.save()
            
            # Get the next URL from session or default to email dashboard
            next_url = request.session.get('next') or reverse('email_app:email_dashboard')
            if 'next' in request.session:
                del request.session['next']
            
            # Log successful login
            logger.info(f"User {email} logged in successfully")
            logger.info(f"Session key after login: {request.session.session_key}")
            logger.info(f"Session data: {dict(request.session)}")
            
            return JsonResponse({
                'status': 'success',
                'redirect_url': next_url
            })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred during login'
            }, status=500)
    
    # For GET requests, just render the login page
    return render(request, 'email_app/login.html')

@require_http_methods(["GET"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """Handle user logout."""
    try:
        email = request.session.get('user_email', 'unknown')
        
        # Store a temporary flag that we're logging out
        request.session['logging_out'] = True
        request.session.modified = True
        
        # Clear all session data
        request.session.flush()
        
        # Log the logout
        logger.info(f"User {email} logged out successfully")
        
        # Create response with cache control headers
        response = HttpResponseRedirect(reverse('email_app:login'))
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
        
    except Exception as e:
        user_email = request.session.get('user_email', 'unknown')
        logger.error(f"Logout error for user {user_email}: {str(e)}", exc_info=True)
        
        # Even on error, redirect to login with cache control
        response = HttpResponseRedirect(reverse('email_app:login'))
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

@require_http_methods(["GET"])
def check_auth(request: HttpRequest) -> JsonResponse:
    """Check if user is authenticated."""
    try:
        # Log request details for debugging
        logger.info(f"Auth check - Session key: {request.session.session_key}")
        logger.info(f"Auth check - Session data: {dict(request.session)}")
        
        # Check if session exists and is valid
        if not request.session.session_key:
            logger.warning("No session key found")
            return JsonResponse({
                'status': 'error',
                'authenticated': False,
                'is_gmail_authenticated': False,
                'message': 'No active session'
            }, status=401)

        # Check Gmail authentication
        is_gmail_auth = request.session.get('is_gmail_authenticated', False)
        user_email = request.session.get('user_email')
        
        if not user_email:
            logger.warning("No user email found in session")
            return JsonResponse({
                'status': 'error',
                'authenticated': False,
                'is_gmail_authenticated': False,
                'message': 'No user email in session'
            }, status=401)
            
        # Update last activity
        request.session['last_activity'] = timezone.now().isoformat()
        
        # Force session save to ensure persistence
        request.session.save()
        
        logger.info(f"Auth check successful for user: {user_email}")
        
        return JsonResponse({
            'status': 'success',
            'authenticated': True,
            'is_gmail_authenticated': is_gmail_auth,
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'authenticated': False,
            'is_gmail_authenticated': False,
            'message': 'Authentication check failed'
        }, status=500)

@require_http_methods(["POST"])
def gmail_auth(request: HttpRequest) -> JsonResponse:
    """Handle Gmail authentication."""
    try:
        data = json.loads(request.body)
        user_email = data.get('email')
        
        if not user_email:
            logger.error("No email provided in request")
            return JsonResponse({
                'error': ERROR_MESSAGES['MISSING_EMAIL']
            }, status=HTTP_STATUS['BAD_REQUEST'])
        
        # Store authentication state in session
        request.session['user_email'] = user_email
        request.session['is_gmail_authenticated'] = True
        request.session['auth_time'] = timezone.now().isoformat()
        request.session.modified = True
        
        logger.info(f"Gmail authentication successful for {user_email}")
        logger.info(f"Session data: {dict(request.session)}")
        
        # Get the next URL from session or default to inbox
        next_url = request.session.pop('next', None) or reverse('email_app:inbox_email')
        
        return JsonResponse({
            'success': True,
            'redirect_url': next_url
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'error': ERROR_MESSAGES['INVALID_REQUEST']
        }, status=HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        logger.error(f"Gmail authentication error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['AUTH_FAILED']
        }, status=HTTP_STATUS['SERVER_ERROR']) 