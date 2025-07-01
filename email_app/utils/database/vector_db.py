import logging
import psycopg2
from django.conf import settings

logger = logging.getLogger(__name__)

def init_vector_db():
    """Initialize vector database connection."""
    try:
        # Connect to vector database
        conn = psycopg2.connect(
            host=settings.VECTOR_DB_CONFIG['host'],
            port=settings.VECTOR_DB_CONFIG['port'],
            database='vector_db',  # Separate database for vectors
            user=settings.VECTOR_DB_CONFIG['user'],
            password=settings.VECTOR_DB_CONFIG['password']
        )
        
        # Create tables if they don't exist
        with conn.cursor() as cur:
            # Create vector_embeddings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id SERIAL PRIMARY KEY,
                    reference_id VARCHAR(255) NOT NULL,
                    embedding_data BYTEA NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index on reference_id
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_embeddings_reference_id 
                ON vector_embeddings(reference_id);
            """)
        
        conn.commit()
        logger.info("Vector database initialized successfully")
        return conn
    except Exception as e:
        logger.error(f"Error initializing vector database: {str(e)}")
        raise

class VectorDatabase:
    """Interface for vector database operations"""
    
    def __init__(self):
        """Initialize vector database connection"""
        self.initialized = False
        self.conn = None
        
        try:
            self.conn = init_vector_db()
            self.initialized = True
            logger.info("Vector database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            raise
    
    def store_embedding(self, reference_id: str, embedding: bytes, metadata: dict = None) -> bool:
        """Store an embedding in the vector database
        
        Args:
            reference_id: ID to reference this embedding (e.g. email_id)
            embedding: The embedding data as bytes
            metadata: Optional metadata about the embedding
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.error("Vector database not initialized")
            return False
            
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vector_embeddings (reference_id, embedding_data, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (reference_id) DO UPDATE
                    SET embedding_data = EXCLUDED.embedding_data,
                        metadata = EXCLUDED.metadata,
                        created_at = CURRENT_TIMESTAMP
                """, (reference_id, embedding, metadata))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_similar_embeddings(self, embedding: bytes, limit: int = 5, 
                             exclude_id: str = None) -> list:
        """Get similar embeddings from the database
        
        Args:
            embedding: The query embedding
            limit: Maximum number of results
            exclude_id: Optional ID to exclude from results
            
        Returns:
            List of similar embeddings with metadata
        """
        if not self.initialized:
            logger.error("Vector database not initialized")
            return []
            
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT reference_id, metadata
                    FROM vector_embeddings
                    WHERE reference_id != %s
                    ORDER BY embedding_data <-> %s
                    LIMIT %s
                """
                cur.execute(query, (exclude_id, embedding, limit))
                results = []
                for row in cur.fetchall():
                    results.append({
                        'reference_id': row[0],
                        'metadata': row[1]
                    })
                return results
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {str(e)}")
            return []
    
    def get_embedding(self, reference_id: str) -> dict:
        """Get an embedding by its reference ID
        
        Args:
            reference_id: The reference ID to look up
            
        Returns:
            Dictionary with embedding data and metadata
        """
        if not self.initialized:
            logger.error("Vector database not initialized")
            return {}
            
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT embedding_data, metadata
                    FROM vector_embeddings
                    WHERE reference_id = %s
                """, (reference_id,))
                result = cur.fetchone()
                if result:
                    embedding_data, metadata = result
                    return {
                        'embedding': embedding_data,
                        'metadata': metadata
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return {}
