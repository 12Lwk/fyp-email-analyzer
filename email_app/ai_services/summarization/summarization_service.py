import logging
from email_app.ai_services.llm.llm_service import LLMService
import json

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for email summarization and analysis"""
    
    def __init__(self, llm_service=None):
        """Initialize the summarization service with Gemini model"""
        self.llm_service = llm_service or LLMService()
        logger.info("Initialized SummarizationService with Gemini model")
    
    def summarize_email(self, email_data):
        """Generate a comprehensive summary of an email using Gemini"""
        try:
            content = email_data.get('content', '')
            subject = email_data.get('subject', '')
            sender = email_data.get('sender', '')
            history = email_data.get('history', [])

            if not content:
                logger.warning("Empty email content provided")
                return self._get_fallback_summary(email_data)

            # Prepare the prompt for Gemini
            prompt = f"""Please analyze the following email and provide a comprehensive summary:

From: {sender}
Subject: {subject}

Content:
{content}

Please provide:
1. A concise summary of the main points
2. Key action items or requests
3. The tone and urgency level
4. Suggested category
5. A template for a professional reply

Format the response as a JSON object with the following keys:
- summary
- key_points (list)
- actions (list)
- priority (High/Medium/Low)
- category
- reply_template"""

            # Generate the analysis using Gemini
            response = self.llm_service.generate_response(prompt)
            
            # Check if response is already a dict
            if isinstance(response, dict):
                if 'error' in response:
                    logger.error(f"LLM service returned error: {response['error']}")
                    return self._get_fallback_summary(email_data)
                    
                # If response has the expected keys, use it directly
                if all(key in response for key in ['summary', 'key_points', 'actions', 'priority', 'category', 'reply_template']):
                    return response
                    
                # If response has a 'response' key, try to parse it as JSON
                if 'response' in response:
                    try:
                        result = json.loads(response['response'])
                        return {
                            'summary': result.get('summary', ''),
                            'key_points': result.get('key_points', []),
                            'actions': result.get('actions', []),
                            'priority': result.get('priority', 'Medium'),
                            'category': result.get('category', 'General'),
                            'reply_template': result.get('reply_template', '')
                        }
                    except (json.JSONDecodeError, TypeError):
                        logger.error("Failed to parse response text as JSON")
                        return self._get_fallback_summary(email_data)
            
            logger.error("Unexpected response format from LLM service")
            return self._get_fallback_summary(email_data)

        except Exception as e:
            logger.error(f"Error in summarize_email: {str(e)}")
            return self._get_fallback_summary(email_data)
    
    def _get_fallback_summary(self, email_data):
        """Generate a fallback summary when Gemini is unavailable"""
        content = email_data.get('content', '')
        subject = email_data.get('subject', '')
        sender = email_data.get('sender', '')

        # Simple text analysis for fallback
        lines = content.split('\n')
        key_points = [line.strip() for line in lines if len(line.strip()) > 20][:3]
        
        # Determine priority based on keywords
        priority = 'Medium'
        if any(word in content.lower() for word in ['urgent', 'immediately', 'asap']):
            priority = 'High'
        elif any(word in content.lower() for word in ['when convenient', 'no rush']):
            priority = 'Low'

        # Determine category based on keywords
        category = 'General'
        if any(word in content.lower() for word in ['meeting', 'schedule', 'appointment']):
            category = 'Scheduling'
        elif any(word in content.lower() for word in ['report', 'data', 'analysis']):
            category = 'Information'
        elif any(word in content.lower() for word in ['problem', 'issue', 'help']):
            category = 'Support'

        return {
            'summary': f"Email from {sender} regarding {subject}",
            'key_points': key_points,
            'actions': ["Review the email content", "Consider a response"],
            'priority': priority,
            'category': category,
            'reply_template': f"Dear {sender.split('@')[0]},\n\nThank you for your email regarding {subject}. I will review it and get back to you soon.\n\nBest regards,"
        }
