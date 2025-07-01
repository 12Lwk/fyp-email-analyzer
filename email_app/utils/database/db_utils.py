import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)

def get_db_connection() -> psycopg2.extensions.connection:
    """Get a connection to the PostgreSQL database.
    
    Returns:
        psycopg2.extensions.connection: Database connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def ensure_db_indexes():
    """Ensure all necessary database indexes exist."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_emails_user_email ON emails(user_email)",
            "CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date)",
            "CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder)",
            "CREATE INDEX IF NOT EXISTS idx_emails_priority ON emails(priority)",
            "CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)",
            "CREATE INDEX IF NOT EXISTS idx_emails_last_modified ON emails(last_modified)"
        ]
        
        for index in indexes:
            cur.execute(index)
            
        conn.commit()
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def process_email_batch(df: pd.DataFrame) -> Dict[str, int]:
    """Process a batch of emails and save to database.
    
    Args:
        df: DataFrame containing email data
        
    Returns:
        Dict containing counts of processed and failed emails
    """
    results = {'processed': 0, 'failed': 0}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for _, row in df.iterrows():
            try:
                # Prepare email data
                email_data = _prepare_email_data(row)
                
                # Insert or update email with all required fields
                query = """
                    INSERT INTO emails (
                        id, user_email, subject, sender, recipients,
                        date, snippet, has_attachments, attachments,
                        star, label, folder, last_modified, priority,
                        priority_score, priority_explanation, priority_last_updated,
                        category, category_confidence, category_last_updated
                    ) VALUES (
                        %(id)s, %(user_email)s, %(subject)s, %(sender)s,
                        %(recipients)s, %(date)s, %(snippet)s,
                        %(has_attachments)s, %(attachments)s, %(star)s,
                        %(label)s, %(folder)s, %(last_modified)s,
                        %(priority)s, %(priority_score)s, %(priority_explanation)s,
                        %(priority_last_updated)s, %(category)s, %(category_confidence)s,
                        %(category_last_updated)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        last_modified = EXCLUDED.last_modified,
                        star = EXCLUDED.star,
                        label = EXCLUDED.label,
                        folder = EXCLUDED.folder,
                        priority = EXCLUDED.priority,
                        priority_score = EXCLUDED.priority_score,
                        priority_explanation = EXCLUDED.priority_explanation,
                        priority_last_updated = EXCLUDED.priority_last_updated,
                        category = EXCLUDED.category,
                        category_confidence = EXCLUDED.category_confidence,
                        category_last_updated = EXCLUDED.category_last_updated
                """
                cur.execute(query, email_data)
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing email: {str(e)}")
                results['failed'] += 1
                continue
        
        conn.commit()
        logger.info(f"Processed {results['processed']} emails, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            
    return results

def _prepare_email_data(row: Tuple) -> Dict[str, Any]:
    """Prepare email data for database insertion.
    
    Args:
        row: Tuple containing email data
        
    Returns:
        Dict containing formatted email data
    """
    return {
        'id': str(row.get('id', '')),
        'user_email': str(row.get('user_email', '')),
        'subject': str(row.get('subject', '')),
        'sender': str(row.get('sender', '')),
        'recipients': row.get('recipients', []),
        'date': row.get('date', datetime.now()),
        'snippet': str(row.get('snippet', '')),
        'has_attachments': bool(row.get('has_attachments', False)),
        'attachments': row.get('attachments', []),
        'star': bool(row.get('star', False)),
        'label': str(row.get('label', '')),
        'folder': str(row.get('folder', 'INBOX')),
        'last_modified': datetime.now(),
        'priority': str(row.get('priority', 'Medium')),
        'priority_score': float(row.get('priority_score', 0.0)),
        'priority_explanation': str(row.get('priority_explanation', '')),
        'priority_last_updated': row.get('priority_last_updated', datetime.now()),
        'category': str(row.get('category', 'General')),
        'category_confidence': float(row.get('category_confidence', 0.0)),
        'category_last_updated': row.get('category_last_updated', datetime.now())
    } 