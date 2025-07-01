import logging
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
import concurrent.futures

from .email_processor import get_email_messages, process_label
from .database.db_utils import process_email_batch
import pandas as pd

logger = logging.getLogger(__name__)

def extract_emails_background(user_email: str) -> None:
    """Extract emails in the background.
    
    Args:
        user_email: Email of the user to extract emails for
    """
    try:
        from ..GMAIL_API.gmail_auth import GmailAuth
        
        # Initialize Gmail service
        gmail_auth = GmailAuth()
        service = gmail_auth.get_gmail_service()
        
        if not service:
            logger.error("Failed to initialize Gmail service")
            return
            
        # Process different labels in parallel
        labels = ['INBOX', 'SENT', 'DRAFT', 'SPAM']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for label in labels:
                future = executor.submit(process_label, service, label)
                futures.append(future)
            
            # Collect results
            all_emails = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    emails = future.result()
                    all_emails.extend(emails)
                except Exception as e:
                    logger.error(f"Error processing label: {str(e)}")
            
            # Convert to DataFrame and process batch
            if all_emails:
                df = pd.DataFrame(all_emails)
                df['user_email'] = user_email
                process_email_batch(df)
                
    except Exception as e:
        logger.error(f"Background extraction error: {str(e)}")

def run_background_task(func, *args, **kwargs) -> threading.Thread:
    """Run a function in a background thread.
    
    Args:
        func: Function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Thread object
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

def periodic_sync(interval: int = 300) -> None:
    """Periodically sync emails.
    
    Args:
        interval: Sync interval in seconds (default: 5 minutes)
    """
    while True:
        try:
            # Get active users
            from django.contrib.auth.models import User
            users = User.objects.filter(is_active=True)
            
            # Sync emails for each user
            for user in users:
                if hasattr(user, 'email'):
                    run_background_task(extract_emails_background, user.email)
            
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Periodic sync error: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying 