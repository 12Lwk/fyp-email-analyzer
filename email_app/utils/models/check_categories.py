import os
from django.db.models import Count
from django.utils import timezone
import logging
from django.core.management.base import BaseCommand
from typing import List

from email_app.models import Email

logger = logging.getLogger(__name__)

def check_categories():
    """Check and update email categories based on frequency."""
    try:
        # Get category counts using gmail_id instead of id
        categories = Email.objects.values('category').annotate(count=Count('gmail_id')).order_by('-count')
        
        # Update category weights based on frequency
        total_emails = Email.objects.count()
        for category_data in categories:
            if category_data['category']:  # Skip None categories
                frequency = category_data['count'] / total_emails
                weight = min(100, int(frequency * 1000))  # Scale frequency to 0-100
                
                Email.objects.filter(id=category_data['category']).update(
                    weight=weight,
                    last_modified=timezone.now()
                )
                
        return True
    except Exception as e:
        logger.error(f"Error checking categories: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    import django
    django.setup()
    check_categories() 