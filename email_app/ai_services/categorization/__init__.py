try:
    from email_app.ai_services.categorization.categorization_service import EmailCategorizationService
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import categorization service: {str(e)}")

__all__ = [
    'EmailCategorizationService'
] 