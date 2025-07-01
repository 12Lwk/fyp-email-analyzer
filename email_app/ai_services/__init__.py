import logging

# Configure logger
logger = logging.getLogger(__name__)

# Try to import EmailCategorizationService
try:
    from email_app.ai_services.categorization.categorization_service import EmailCategorizationService
    logger.info("Successfully imported EmailCategorizationService")
except ImportError as e:
    logger.warning(f"Could not import categorization service: {str(e)}")
    # Define a fallback class if the import fails
    class EmailCategorizationService:
        def __init__(self):
            logger.warning("Using fallback EmailCategorizationService")
            self.categories = ["Personal Email"]
            
        def categorize_email(self, email_data):
            return {
                'category': "Personal Email",
                'confidence': 0.1,
                'explanation': "Default category (import failed)"
            }

# Define what should be imported from this package
__all__ = ['EmailCategorizationService'] 