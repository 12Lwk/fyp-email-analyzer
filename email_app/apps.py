from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class EmailAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_app'
    
    def ready(self):
        """Initialize app components when Django starts."""
        try:
            # Import here to avoid circular imports
            from .ai_services.llm.llm_service import LLMService
            from .ai_services.embeddings.embedding_utils import EmbeddingService
            from .ai_services.recommendations.recommendation_service import RecommendationService
            from .ai_services.summarization.summarization_service import SummarizationService
            
            # Initialize services
            self.llm_service = LLMService()
            self.embedding_service = EmbeddingService()
            self.recommendation_service = RecommendationService()
            self.summarization_service = SummarizationService()
            
            logger.info("Email app services initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import AI service: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing email app: {str(e)}", exc_info=True)
