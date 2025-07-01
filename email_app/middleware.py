from django.utils import timezone
from django.conf import settings
import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)

class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip checking for authentication on the login page and logout URL
        if request.path == reverse('email_app:login') or request.path == reverse('email_app:logout'):
            return self.get_response(request)
            
        # Only process if session exists
        if hasattr(request, 'session'):
            # Check if Gmail authentication is still valid
            if not request.session.get('is_gmail_authenticated'):
                logger.warning("Gmail authentication expired")
                # Use HttpResponseRedirect for more reliable redirection
                response = HttpResponseRedirect(reverse('email_app:login'))
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            
            # Update last activity timestamp
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Log session activity for debugging
            logger.info(f"Session activity - User: {request.session.get('user_email')}")
            logger.info(f"Session activity - Session key: {request.session.session_key}")
            logger.info(f"Session activity - Gmail auth: {request.session.get('is_gmail_authenticated')}")
            
            # Force session save to ensure persistence
            request.session.modified = True
            request.session.save()

        response = self.get_response(request)
        
        # Add cache control headers to all responses
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response 