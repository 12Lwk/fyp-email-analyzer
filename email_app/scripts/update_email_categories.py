import os
import sys
import logging
import django
from django.db import transaction
from tqdm import tqdm
from datetime import datetime

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_project.settings')
django.setup()

from email_app.models import Emails
from email_app.utils.category_model_loader_v4 import EmailCategoryModelV4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_category_updates.log'),
        logging.StreamHandler()
    ]
)

def update_email_categories():
    try:
        model = EmailCategoryModelV4()
        emails = Emails.objects.filter(
            category__isnull=True
        ) | Emails.objects.filter(
            category_confidence__lt=0.3
        )
        
        for email in emails:
            prediction = model.predict_category(
                email.subject,
                email.snippet
            )
            
            email.category = prediction['category']
            email.category_confidence = prediction['confidence']
            email.category_last_updated = datetime.now()
            email.save()
            
    except Exception as e:
        logging.error(f"Error during category update: {str(e)}")
        raise

if __name__ == "__main__":
    update_email_categories() 