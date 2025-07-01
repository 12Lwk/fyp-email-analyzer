import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from email_app.utils.database.vector_db import VectorDatabase
from email_app.ai_services.llm.llm_service import LLMService

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Utility class for generating embeddings using TF-IDF"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=384,  # Match the size of MiniLM embeddings
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.is_fitted = False
        logger.info("TF-IDF Embedding Generator initialized")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using TF-IDF"""
        try:
            if not self.is_fitted:
                # Fit the vectorizer with a dummy document
                self.vectorizer.fit(['dummy document'])
                self.is_fitted = True
            
            # Transform the text into a TF-IDF vector
            embedding = self.vectorizer.transform([text]).toarray()[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return list(np.random.rand(384))  # Return random vector as fallback

# Create a singleton instance
embedding_generator = EmbeddingGenerator()

# Export the generate_embedding function
def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text"""
    return embedding_generator.generate_embedding(text)

class EmbeddingService:
    """Service for managing text embeddings"""
    
    def __init__(self, llm_service=None):
        """Initialize the embedding service"""
        self.llm_service = llm_service or LLMService()
        self.vector_db = VectorDatabase()
        logger.info("Embedding Service initialized")
    
    def store_email_embedding(self, email_id: str, email_data: Dict[str, Any]) -> bool:
        """Store email embedding in vector database"""
        try:
            # Combine subject and content for embedding
            subject = email_data.get("subject", "")
            content = email_data.get("content", "")
            combined_text = f"{subject}\n\n{content}"
            
            # Generate embedding
            embedding = self.generate_embedding(combined_text)
            if embedding is None:
                logger.error("Failed to generate embedding")
                return False
            
            # Store in vector DB
            return self.vector_db.store_email_embedding(email_id, embedding, email_data)
        except Exception as e:
            logger.error(f"Error storing email embedding: {str(e)}")
            return False
    
    def find_similar_emails(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar emails based on text similarity"""
        try:
            # Generate embedding for query
            embedding = self.generate_embedding(query_text)
            
            if embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Find similar emails
            return self.vector_db.find_similar_emails(embedding, limit)
        except Exception as e:
            logger.error(f"Error finding similar emails: {str(e)}")
            return []

    def generate_embedding(self, text):
        """Generate embedding using Gemini's embedding model"""
        try:
            if not text:
                logger.warning("Empty text provided for embedding")
                return self._get_fallback_embedding(text)

            # Generate embedding using Gemini
            embedding = self.llm_service.generate_embedding(text)
            
            # Ensure the embedding is a numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            
            # Normalize the embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error in generate_embedding: {str(e)}")
            return self._get_fallback_embedding(text)

    def _get_fallback_embedding(self, text):
        """Generate a fallback embedding when Gemini is unavailable"""
        # Return a zero vector of appropriate dimension
        return [0.0] * 384  # Using 384 dimensions to match Gemini's embedding size
