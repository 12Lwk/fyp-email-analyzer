import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from email_app.ai_services.llm.llm_service import LLMService
from email_app.ai_services.embeddings.embedding_utils import EmbeddingService
from email_app.utils.database.vector_db import VectorDatabase

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service for generating email recommendations and summaries"""
    
    def __init__(self, llm_service=None):
        """Initialize the recommendation service with Gemini model"""
        self.llm_service = llm_service or LLMService()
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDatabase()
        logger.info("Initialized RecommendationService with Gemini model")
    
    def generate_summary(self, email_content: str, subject: str = "") -> str:
        """Generate a summary of the email content"""
        try:
            # Prepare the prompt for summarization
            prompt = f"""Please provide a concise summary of the following email:

Subject: {subject}

Content:
{email_content}

Summary:"""
            
            # Get summary from LLM
            summary = self.llm_service.generate_response(prompt, max_tokens=500)
            
            if not summary:
                logger.warning("Empty summary received from LLM, generating fallback summary")
                return self._generate_fallback_summary(email_content, subject)
            
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._generate_fallback_summary(email_content, subject)
    
    def generate_recommendations(self, content, subject, sender):
        """Generate recommendations using Gemini model"""
        try:
            if not content:
                logger.warning("Empty content provided for recommendations")
                return self._get_fallback_recommendations(content, subject, sender)

            # Prepare the prompt for Gemini
            prompt = f"""Please analyze the following email and provide recommendations:

From: {sender}
Subject: {subject}

Content:
{content}

Please provide:
1. Key action items or requests
2. Priority level (High/Medium/Low)
3. Suggested category
4. A template for a professional reply
5. Similar topics or related actions

Format the response as a JSON object with the following keys:
- key_points (list)
- actions (list)
- priority (High/Medium/Low)
- category
- reply_template
- related_topics (list)"""

            # Generate the analysis using Gemini
            response = self.llm_service.generate_response(prompt)
            
            # Parse the response
            try:
                import json
                result = json.loads(response)
            except json.JSONDecodeError:
                logger.error("Failed to parse Gemini response as JSON")
                return self._get_fallback_recommendations(content, subject, sender)

            return {
                'key_points': result.get('key_points', []),
                'actions': result.get('actions', []),
                'priority': result.get('priority', 'Medium'),
                'category': result.get('category', 'General'),
                'reply_template': result.get('reply_template', ''),
                'related_topics': result.get('related_topics', [])
            }

        except Exception as e:
            logger.error(f"Error in generate_recommendations: {str(e)}")
            return self._get_fallback_recommendations(content, subject, sender)
    
    def _get_fallback_recommendations(self, content, subject, sender):
        """Generate fallback recommendations when Gemini is unavailable"""
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

        # Generate basic actions
        actions = ["Review the email content", "Consider a response"]
        if '?' in content:
            actions.append("Address the questions in the email")
        if any(word in content.lower() for word in ['meeting', 'schedule', 'appointment']):
            actions.append("Check calendar availability")
        if any(word in content.lower() for word in ['attachment', 'file', 'document']):
            actions.append("Review any attachments")

        return {
            'key_points': key_points,
            'actions': actions,
            'priority': priority,
            'category': category,
            'reply_template': f"Dear {sender.split('@')[0]},\n\nThank you for your email regarding {subject}. I will review it and get back to you soon.\n\nBest regards,",
            'related_topics': []
        }
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format email history for the prompt"""
        if not history:
            return "No previous interactions"
        
        formatted = []
        for email in history[:5]:  # Limit to last 5 emails
            formatted.append(f"Date: {email.get('date', 'Unknown')}")
            formatted.append(f"Subject: {email.get('subject', 'No Subject')}")
            formatted.append(f"Content: {email.get('content', '')[:200]}...")
            formatted.append("---")
        
        return "\n".join(formatted)
    
    def _parse_recommendations(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured recommendations"""
        try:
            # Initialize default structure
            recommendations = {
                'key_points': [],
                'actions': [],
                'priority': 'Medium',
                'category': 'General',
                'reply_template': '',
                'similar_emails': []
            }
            
            # Split response into sections
            sections = response.split('\n\n')
            
            for section in sections:
                if section.startswith('Key points:'):
                    recommendations['key_points'] = [
                        point.strip('- ').strip() 
                        for point in section.split('\n')[1:] 
                        if point.strip()
                    ]
                elif section.startswith('Suggested actions:'):
                    recommendations['actions'] = [
                        action.strip('- ').strip() 
                        for action in section.split('\n')[1:] 
                        if action.strip()
                    ]
                elif section.startswith('Priority level:'):
                    priority = section.split(':')[1].strip()
                    if priority in ['High', 'Medium', 'Low']:
                        recommendations['priority'] = priority
                elif section.startswith('Category:'):
                    recommendations['category'] = section.split(':')[1].strip()
                elif section.startswith('Suggested reply template:'):
                    recommendations['reply_template'] = '\n'.join(section.split('\n')[1:]).strip()
            
            return recommendations
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            return self._get_default_recommendations()
    
    def _generate_fallback_summary(self, email_content: str, subject: str) -> str:
        """Generate a fallback summary when LLM is not available"""
        # Extract first few sentences as summary
        sentences = email_content.split('.')
        summary = []
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Only consider meaningful sentences
                summary.append(sentence.strip())
                if len(summary) >= 3:  # Limit to 3 sentences
                    break
        
        return f"Summary of '{subject}':\n" + "\n".join(f"- {s}" for s in summary)
    
    def _generate_fallback_recommendations(self, email_content: str, subject: str, sender: str) -> Dict[str, Any]:
        """Generate fallback recommendations when LLM is not available"""
        return {
            'key_points': self._extract_key_points(email_content),
            'actions': self._suggest_actions(email_content),
            'priority': self._determine_priority(email_content),
            'category': self._determine_category(email_content),
            'reply_template': self._generate_reply_template(sender, subject),
            'similar_emails': []
        }
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text"""
        sentences = text.split('.')
        key_points = []
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Only consider meaningful sentences
                key_points.append(sentence.strip())
                if len(key_points) >= 3:  # Limit to 3 key points
                    break
        return key_points
    
    def _suggest_actions(self, text: str) -> List[str]:
        """Suggest actions based on email content"""
        actions = ["Review the email content carefully"]
        
        if '?' in text:
            actions.append("Respond to the questions in the email")
        
        if any(word in text.lower() for word in ['attachment', 'attached', 'file']):
            actions.append("Check the attached files")
        
        if any(word in text.lower() for word in ['meeting', 'schedule', 'calendar']):
            actions.append("Add event to your calendar")
        
        if any(word in text.lower() for word in ['urgent', 'immediately', 'asap']):
            actions.append("Prioritize this email for immediate action")
        
        return actions
    
    def _determine_priority(self, text: str) -> str:
        """Determine priority level based on content"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['urgent', 'immediately', 'asap', 'emergency']):
            return "High"
        elif any(word in text_lower for word in ['important', 'attention', 'critical']):
            return "Medium"
        return "Low"
    
    def _determine_category(self, text: str) -> str:
        """Determine email category"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['meeting', 'schedule', 'appointment']):
            return "Scheduling"
        elif any(word in text_lower for word in ['report', 'data', 'analysis']):
            return "Information Request"
        elif any(word in text_lower for word in ['problem', 'issue', 'help']):
            return "Support"
        return "General"
    
    def _generate_reply_template(self, sender: str, subject: str) -> str:
        """Generate a basic reply template"""
        greeting = f"Dear {sender.split('@')[0] if sender else 'there'},"
        body = "Thank you for your email. I have received your message and will review it carefully."
        closing = "\n\nBest regards,"
        
        return f"{greeting}\n\n{body}\n{closing}"
    
    def _get_default_recommendations(self) -> Dict[str, Any]:
        """Get default recommendations structure"""
        return {
            'key_points': ["Unable to extract key points"],
            'actions': ["Review the email content manually"],
            'priority': 'Medium',
            'category': 'General',
            'reply_template': "Dear [Name],\n\nThank you for your email. I will review it and get back to you soon.\n\nBest regards,",
            'similar_emails': []
        }
    
    def generate_action_suggestions(self, email_content: str, subject: str = "", sender: str = "", category: str = "", priority: str = "") -> List[str]:
        """Generate suggested actions for an email
        
        Args:
            email_content: The content/body of the email
            subject: The email subject line
            sender: The email sender
            category: The email category
            priority: The email priority
            
        Returns:
            List of suggested actions
        """
        # Truncate email content if it's too long
        content_shortened = email_content[:3000] if len(email_content) > 3000 else email_content
        
        # Create a more detailed prompt for the LLM
        prompt = f"""Based on the following email, suggest 3-5 specific actions the user should take, considering the context, category ({category}), and priority ({priority}):

Subject: {subject}
From: {sender}

{content_shortened}

Action suggestions (each on a new line):
1."""

        try:
            suggestions_text = self.llm_service.generate_response(prompt, max_length=200)
            
            # Process the suggestions
            raw_suggestions = suggestions_text.split('\n')
            
            # Clean up and format suggestions
            suggestions = []
            for suggestion in raw_suggestions:
                # Remove leading numbers and symbols
                clean_suggestion = suggestion.strip()
                clean_suggestion = clean_suggestion.lstrip("0123456789.- ")
                
                if clean_suggestion and len(clean_suggestion) > 5:  # Avoid empty or very short suggestions
                    suggestions.append(clean_suggestion)
            
            return suggestions
        except Exception as e:
            logger.error(f"Error generating action suggestions: {str(e)}")
            return ["Review the email contents carefully", 
                    "Consider responding if a response is required"]
    
    def find_similar_emails(self, email_content: str, email_id: str) -> List[Dict[str, Any]]:
        """Find emails similar to the current one
        
        Args:
            email_content: The content/body of the email
            email_id: The current email's ID
            
        Returns:
            List of similar emails with metadata
        """
        try:
            # Generate embedding for the current email
            embedding = self.llm_service.generate_embedding(email_content)
            
            if not embedding:
                logger.error("Failed to generate embedding for similarity search")
                return []
            
            # Search for similar emails in vector DB
            similar_emails = self.vector_db.find_similar_emails(embedding, limit=5)
            
            # Format results
            results = []
            for item in similar_emails:
                # Skip the current email
                if item.id == email_id:
                    continue
                
                results.append({
                    "id": item.id,
                    "subject": item.payload.get("subject", "No Subject"),
                    "sender": item.payload.get("sender", "Unknown"),
                    "date": item.payload.get("date", ""),
                    "similarity_score": item.score,
                    "snippet": item.payload.get("snippet", "")[:150] + "..."
                })
            
            return results
        except Exception as e:
            logger.error(f"Error finding similar emails: {str(e)}")
            return []
    
    def suggest_reply(self, email_content: str, subject: str = "", sender: str = "", category: str = "", priority: str = "") -> str:
        """Suggest a reply for the email
        
        Args:
            email_content: The content/body of the email
            subject: The email subject line
            sender: The email sender
            category: The email category
            priority: The email priority
            
        Returns:
            Suggested reply text
        """
        # Truncate email content if it's too long
        content_shortened = email_content[:2000] if len(email_content) > 2000 else email_content
        
        # Create a more detailed prompt for the LLM
        prompt = f"""Write a professional reply to the following email, addressing any questions or requests and maintaining a polite tone. Consider the email's category ({category}) and priority ({priority}):

Subject: {subject}
From: {sender}

{content_shortened}

Reply:"""

        try:
            reply = self.llm_service.generate_response(prompt, max_length=300)
            return reply
        except Exception as e:
            logger.error(f"Error generating reply suggestion: {str(e)}")
            return "Could not generate a reply suggestion."
    
    def store_email_for_recommendations(self, email_id: str, email_data: Dict[str, Any]) -> bool:
        """Store email in vector DB for future recommendations
        
        Args:
            email_id: Unique ID for the email
            email_data: Dictionary with email metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create text for embedding - combine subject and content
            subject = email_data.get("subject", "")
            content = email_data.get("content", "")
            
            text_for_embedding = f"{subject}\n\n{content}"
            
            # Generate embedding
            embedding = self.llm_service.generate_embedding(text_for_embedding)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for email {email_id}")
                return False
            
            # Store in vector DB
            return self.vector_db.store_email_embedding(email_id, embedding, email_data)
        except Exception as e:
            logger.error(f"Error storing email for recommendations: {str(e)}")
            return False
