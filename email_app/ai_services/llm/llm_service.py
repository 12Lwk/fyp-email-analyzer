import logging
import os
import json
from typing import Dict, List, Optional, Union
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LLMService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM service with Gemini model."""
        # Skip if already initialized
        if self._initialized:
            return
            
        # Don't initialize immediately - wait for first use
        self.model = None
        self.embedding_model = None
        self._initialized = True
    
    def _ensure_initialized(self) -> bool:
        """Initialize the LLM service if not already initialized."""
        if self.model is not None:
            return True
            
        try:
            # Import here to avoid circular imports
            import google.generativeai as genai
            from dotenv import load_dotenv
            
            logger.info("Starting LLM service initialization...")
            
            # Load environment variables
            load_dotenv()
            logger.info("Environment variables loaded")
            
            api_key = os.getenv('GOOGLE_API_KEY', '').strip()
            if not api_key:
                logger.error("Google API key not found in environment variables")
                return False
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            
            # Configure generation parameters for consistent, structured responses
            self.generation_config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent responses
                max_output_tokens=2048,
                candidate_count=1,
                top_p=0.8,
                top_k=40
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False
    
    def generate_response(self, prompt: str) -> dict:
        """Generate a response using the LLM service."""
        try:
            if not self._ensure_initialized():
                logger.error("LLM service initialization failed")
                return self._get_fallback_response(prompt)

            # Extract current user information from the prompt
            lines = prompt.split('\n')
            current_user = next((line.split(':')[1].strip() for line in lines if line.lower().startswith('current user:')), '')
            current_email = next((line.split(':')[1].strip() for line in lines if line.lower().startswith('current email:')), '')
            
            # If no user name found, use email username
            if not current_user and current_email and '@' in current_email:
                current_user = current_email.split('@')[0]
            
            # Log the user information
            logger.info(f"Using user information from request: {current_user}")
            
            # Generate response with structured prompt including user info
            response = self.model.generate_content(
                self._get_structured_prompt(prompt, current_user, current_email),
                generation_config=self.generation_config
            )
            
            if not response or not response.text:
                logger.error("Empty response from LLM service")
                return self._get_fallback_response(prompt, current_user)
            
            try:
                # Clean the response text
                response_text = response.text.strip()
                
                # Remove any markdown formatting
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                # Ensure the JSON is properly terminated
                response_text = response_text.strip()
                if not response_text.endswith('}'):
                    response_text += '}'
                
                logger.info(f"Cleaned response text: {response_text}")
                
                # Parse JSON response
                result = json.loads(response_text)
                
                # Validate and format the response
                formatted_response = {
                    'summary': str(result.get('summary', '')).strip(),
                    'key_points': result.get('key_points', []),
                    'actions': result.get('actions', []),
                    'priority': str(result.get('priority', 'medium')).lower().strip(),
                    'category': str(result.get('category', 'other')).lower().strip(),
                    'reply_template': str(result.get('reply_template', '')).strip()
                }

                # Ensure non-empty summary
                if not formatted_response['summary']:
                    formatted_response['summary'] = 'No summary available'

                # Validate priority
                if formatted_response['priority'] not in ['high', 'medium', 'low']:
                    formatted_response['priority'] = 'medium'
                
                # Validate category
                if formatted_response['category'] not in ['business', 'personal', 'urgent', 'promotional', 'social media', 'IT alerts', 'other']:
                    formatted_response['category'] = 'other'
                
                # Ensure lists are properly formatted
                if not isinstance(formatted_response['key_points'], list) or not formatted_response['key_points']:
                    formatted_response['key_points'] = ['No key points available']
                if not isinstance(formatted_response['actions'], list) or not formatted_response['actions']:
                    formatted_response['actions'] = ['No actions available']
                
                # Handle reply template and signature
                if not formatted_response['reply_template']:
                    formatted_response['reply_template'] = 'Thank you for your email. I will review your message and respond accordingly.'

                # Clean up any existing signature
                formatted_response['reply_template'] = re.sub(
                    r'\s*(?:Best regards|Sincerely|Kind regards),?.*$',
                    '',
                    formatted_response['reply_template'].rstrip()
                )

                # Add the signature with username
                if current_user:
                    formatted_response['reply_template'] = formatted_response['reply_template'].rstrip() + f'\n\nBest regards,\n{current_user}'
                else:
                    formatted_response['reply_template'] = formatted_response['reply_template'].rstrip() + '\n\nBest regards'
                
                return formatted_response
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                return self._get_fallback_response(prompt, current_user)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(prompt, current_user)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using the Gemini embedding model."""
        self._ensure_initialized()
        if not self.model:
            return self._get_fallback_embedding(text)
            
        try:
            embedding = self.embedding_model.generate_content(text)
            return embedding.embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return self._get_fallback_embedding(text)

    def _get_structured_prompt(self, email_content: str, current_user: str, current_email: str) -> str:
        """Create a structured prompt for email analysis."""
        # Extract sender and recipient information
        lines = email_content.split('\n')
        sender = next((line for line in lines if line.lower().startswith('from:')), '')
        recipient = next((line for line in lines if line.lower().startswith('to:')), '')
        
        # Extract names and emails
        sender_name = ''
        sender_email = ''
        
        # Handle From field
        if sender:
            if '<' in sender:
                # Format: "Name <email@example.com>"
                sender_name = sender.split('<')[0].replace('From:', '').strip()
                sender_email = sender.split('<')[1].replace('>', '').strip()
            else:
                # Format: "From: email@example.com" or just "email@example.com"
                sender_email = sender.replace('From:', '').strip()
                # For no-reply or system emails, use the domain part as name
                if 'noreply' in sender_email.lower() or 'no-reply' in sender_email.lower():
                    domain = sender_email.split('@')[1].split('.')[0].title()
                    sender_name = f"{domain} Team"
                else:
                    sender_name = sender_email.split('@')[0]

        # Clean up sender name
        sender_name = sender_name.replace('From:', '').strip()
        if not sender_name:
            if 'noreply' in sender_email.lower() or 'no-reply' in sender_email.lower():
                domain = sender_email.split('@')[1].split('.')[0].title()
                sender_name = f"{domain} Team"
            else:
                sender_name = sender_email.split('@')[0] if '@' in sender_email else 'Support Team'
            
        logger.info(f"Extracted sender name: {sender_name}, email: {sender_email}")
        
        return f"""Analyze the following email and provide a response in JSON format (without markdown tags):

        Current User Information:
        - Name: {current_user}
        - Email: {current_email}

        Email Content:
        {email_content}

        Sender Information:
        - Name: {sender_name}
        - Email: {sender_email}

        Return your analysis as a clean JSON object with the following structure:
        {{
            "summary": "Provide a concise summary of the main purpose or message of the email",
            "key_points": [
                "Identify and list the most critical points or topics mentioned in the email"
            ],
            "actions": [
                "List any follow-up actions, deadlines, or decisions required based on the email content"
            ],
            "priority": "high|medium|low",
            "category": "business|personal|urgent|promotional|social media|IT alerts|other",
            "reply_template": "Generate a brief and professional reply that acknowledges the email and addresses the key message or required actions. Use the exact sender name in the greeting and {current_user} in the signature."
        }}

        Guidelines:
        - Keep the summary concise and clear
        - Extract 2-3 key points directly from the email
        - Suggest 2-3 practical actions based on the content
        - Set priority based on urgency and importance
        - Choose the most appropriate category
        - Make the reply template professional and relevant to the email content
        - For system emails (no-reply), use the service name (e.g., "Dear Google Team,")
        - Use {current_user} in the signature
        - NEVER use placeholders like [Your Name], [Name], etc.
        - Do not include multiple signatures or "Best regards"

        Important: Return ONLY the JSON object without any markdown tags or additional text.

        Rules:
        1. Priority must be one of: high, medium, low (lowercase)
        2. Category must be one of: business, personal, urgent, promotional, other (lowercase)
        3. All fields are required
        4. key_points and actions must be lists
        5. Ensure the response is valid JSON
        6. Keep the reply template concise and professional
        7. Base priority on urgency, sender importance, and content
        8. Choose category based on email content and context
        9. For system/no-reply emails, use the service name in greeting
        10. Use {current_user} in the signature, do not add additional signatures

        Return ONLY the JSON object, no additional text."""

    def _get_fallback_response(self, email_content: str, current_user: str = None) -> dict:
        """Generate a fallback response when LLM service fails."""
        # Extract basic info from email content
        lines = email_content.split('\n')
        subject = next((line for line in lines if line.lower().startswith('subject:')), 'No subject')
        sender_line = next((line for line in lines if line.lower().startswith('from:')), '')
        
        # Extract sender name and email
        sender_name = ''
        sender_email = ''
        if '<' in sender_line:
            sender_name = sender_line.split('<')[0].replace('From:', '').strip()
            sender_email = sender_line.split('<')[1].replace('>', '').strip()
        else:
            sender_email = sender_line.replace('From:', '').strip()
            sender_name = sender_email.split('@')[0] if '@' in sender_email else sender_email
        
        # Clean up sender name
        if not sender_name or sender_name.lower() == 'from:':
            if sender_email.lower().includes('noreply') or sender_email.lower().includes('no-reply'):
                domain = sender_email.split('@')[1].split('.')[0]
                sender_name = f"{domain.title()} Team"
            else:
                sender_name = sender_email.split('@')[0] if '@' in sender_email else 'Support Team'
        
        # Create reply template sections with explicit line breaks
        sections = [
            f"Dear {sender_name}",  # No comma here as it will be added by the frontend formatting
            "Thank you for your email. I will review your message and respond accordingly",
            "Best regards",
            current_user
        ]
        
        # Join with special marker for line breaks that the frontend will handle
        reply_template = ". ".join(sections)
        
        return {
            'summary': f"Email from {sender_name} with subject {subject.replace('Subject:', '').strip()}",
            'key_points': ['Email content requires review'],
            'actions': ['Review email contents', 'Determine appropriate response'],
            'priority': 'medium',
            'category': 'other',
            'reply_template': reply_template
        }

    def _get_fallback_embedding(self, text):
        """Generate a simple fallback embedding"""
        # Return a zero vector of appropriate dimension
        return [0.0] * 384  # Using 384 dimensions to match previous implementation
