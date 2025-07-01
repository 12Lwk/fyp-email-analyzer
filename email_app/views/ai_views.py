import logging
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, TypedDict

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from ..utils.constants import ERROR_MESSAGES, HTTP_STATUS
from ..models import Email
from ..ai_services.summarization.summarization_service import SummarizationService
from ..ai_services.recommendations.recommendation_service import RecommendationService
from ..ai_services.embeddings.embedding_utils import EmbeddingService
from ..ai_services.llm.llm_service import LLMService
from ..ai_services.exceptions import AIServiceError, ModelNotReadyError

logger = logging.getLogger(__name__)

# Type definitions
class EmailAnalysisResult(TypedDict):
    success: bool
    summary: str
    key_points: List[str]
    actions: List[str]
    priority: str
    category: str
    suggested_reply: str
    similar_emails: List[Dict[str, Any]]
    diagnostic_info: Dict[str, str]

# Initialize services with LLM service
llm_service = LLMService()
summarization_service = SummarizationService(llm_service=llm_service)
recommendation_service = RecommendationService(llm_service=llm_service)
embedding_service = EmbeddingService(llm_service=llm_service)

def get_fallback_response(data: Dict[str, Any]) -> EmailAnalysisResult:
    """Generate a fallback response when analysis fails.
    
    Args:
        data: Dictionary containing email data
        
    Returns:
        Fallback analysis result
    """
    result = summarization_service._get_fallback_summary({
        'content': data.get('content', ''),
        'subject': data.get('subject', ''),
        'sender': data.get('sender', '')
    })
    
    return {
        'success': True,
        'summary': result.get('summary', ''),
        'key_points': result.get('key_points', []),
        'actions': result.get('actions', []),
        'priority': result.get('priority', 'Medium'),
        'category': result.get('category', 'General'),
        'suggested_reply': result.get('reply_template', ''),
        'similar_emails': [],
        'diagnostic_info': {
            'provider': 'fallback',
            'mode': 'timeout',
            'timestamp': str(datetime.now())
        }
    }

@csrf_exempt
@require_POST
def analyze_email(request: HttpRequest, email_id: Optional[str] = None) -> JsonResponse:
    """API endpoint to analyze an email with AI services.
    
    Args:
        request: The HTTP request object containing email data
        email_id: Optional ID of the email to analyze
        
    Returns:
        JSON response with analysis results or error message
        
    Raises:
        AIServiceError: If AI analysis fails
        ValidationError: If request data is invalid
        json.JSONDecodeError: If request body is not valid JSON
    """
    try:
        # Set a short timeout for the operation to avoid long waits
        response_data: Optional[EmailAnalysisResult] = None
        analysis_error: Optional[str] = None
        analysis_complete = threading.Event()
        
        def perform_analysis() -> None:
            nonlocal response_data, analysis_error
            try:
                # Parse and validate request data
                try:
                    request_body = request.body.decode('utf-8')
                    data = json.loads(request_body)
                except UnicodeDecodeError:
                    logger.error("Failed to decode request body as UTF-8")
                    analysis_error = "Invalid request encoding"
                    return
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse request body as JSON: {str(e)}")
                    analysis_error = "Invalid JSON format"
                    return

                content = data.get('content', '')
                subject = data.get('subject', '')
                sender = data.get('sender', '')
                
                if not content:
                    raise ValidationError('Email content is required for analysis')
                
                # Log the request
                logger.info(f"Analyze email request received. Content length: {len(content)}, Subject: {subject[:30]}...")
                
                # Generate analysis
                logger.debug(f"Generating summary for email with subject: {subject}")
                result = summarization_service.summarize_email({
                    'content': content,
                    'subject': subject,
                    'sender': sender,
                    'history': []  # Add history if available
                })
                logger.debug(f"Generated summary: {result.get('summary', '')}")
                
                # Get similar emails if we have an email ID
                similar_emails = []
                if email_id:
                    similar_emails = embedding_service.find_similar_emails(content, limit=3)
                
                # Prepare response
                response_data = {
                    'success': True,
                    'summary': result.get('summary', ''),
                    'key_points': result.get('key_points', []),
                    'actions': result.get('actions', []),
                    'priority': result.get('priority', 'Medium'),
                    'category': result.get('category', 'General'),
                    'suggested_reply': result.get('reply_template', ''),
                    'similar_emails': similar_emails,
                    'diagnostic_info': {
                        'provider': 'summarization_service',
                        'timestamp': str(datetime.now())
                    }
                }
                
                logger.info("Analysis completed successfully")
                
            except ValidationError as e:
                logger.warning(f"Validation error in analysis: {str(e)}")
                analysis_error = str(e)
            except AIServiceError as e:
                logger.error(f"AI service error in analysis: {str(e)}", exc_info=True)
                analysis_error = str(e)
            except Exception as e:
                logger.error(f"Unexpected error in analysis thread: {str(e)}", exc_info=True)
                analysis_error = str(e)
            finally:
                analysis_complete.set()
        
        # Start analysis in a separate thread
        analysis_thread = threading.Thread(target=perform_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Wait for analysis to complete or timeout
        if not analysis_complete.wait(timeout=10):  # 10 second timeout
            logger.warning("Analysis timeout reached, returning fallback response")
            data = json.loads(request.body)
            return JsonResponse(get_fallback_response(data))
        
        # Handle analysis results
        if analysis_error:
            logger.error(f"Analysis error: {analysis_error}")
            return JsonResponse({
                'error': ERROR_MESSAGES['ai_analysis_error'],
                'details': analysis_error
            }, status=HTTP_STATUS['processing_error'])
        
        if response_data:
            return JsonResponse(response_data)
        
        # Handle unexpected state
        logger.error("Unexpected state: analysis complete but no response or error")
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': 'Invalid JSON format in request body'
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Unexpected error in analyze_email view: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:serve_login')
def store_email_embedding(request: HttpRequest, email_id: str) -> JsonResponse:
    """API endpoint to store an email's embedding vector.
    
    Args:
        request: The HTTP request object containing embedding data
        email_id: ID of the email to store embedding for
        
    Returns:
        JSON response indicating success or failure
        
    Raises:
        AIServiceError: If embedding storage fails
        ValidationError: If request data is invalid
    """
    try:
        # Parse and validate request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': 'Invalid JSON format in request body'
            }, status=HTTP_STATUS['bad_request'])
        
        # Store embedding
        try:
            success = embedding_service.store_email_embedding(email_id, data)
        except AIServiceError as e:
            logger.error(f"AI service error storing embedding: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': ERROR_MESSAGES['ai_service_error'],
                'details': str(e)
            }, status=HTTP_STATUS['bad_gateway'])
        
        if success:
            logger.info(f"Successfully stored embedding for email {email_id}")
            return JsonResponse({
                'success': True,
                'message': f'Successfully stored embedding for email {email_id}'
            })
        else:
            logger.warning(f"Failed to store embedding for email {email_id}")
            return JsonResponse({
                'success': False,
                'error': ERROR_MESSAGES['processing_error']
            }, status=HTTP_STATUS['server_error'])
            
    except Exception as e:
        logger.error(f"Unexpected error storing email embedding: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@require_GET
@login_required(login_url='email_app:serve_login')
def similar_emails(request: HttpRequest, email_id: str) -> JsonResponse:
    """API endpoint to find similar emails using embedding similarity.
    
    Args:
        request: The HTTP request object
        email_id: ID of the email to find similar emails for
        
    Returns:
        JSON response with list of similar emails
        
    Raises:
        Email.DoesNotExist: If email_id is not found
        AIServiceError: If similarity search fails
        ValidationError: If parameters are invalid
    """
    try:
        # Validate and get parameters
        try:
            limit = max(1, min(int(request.GET.get('limit', 5)), 10))
        except ValueError:
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': 'Invalid limit parameter'
            }, status=HTTP_STATUS['bad_request'])
        
        # Get email content
        try:
            email_obj = get_object_or_404(Email, id=email_id)
        except Email.DoesNotExist:
            return JsonResponse({
                'error': ERROR_MESSAGES['not_found'],
                'details': f'Email {email_id} not found'
            }, status=HTTP_STATUS['not_found'])
        
        # Find similar emails
        try:
            similar_emails = embedding_service.find_similar_emails(
                email_obj.body,
                limit=limit
            )
            
            logger.info(f"Found {len(similar_emails)} similar emails for {email_id}")
            return JsonResponse({
                'success': True,
                'similar_emails': similar_emails
            })
            
        except AIServiceError as e:
            logger.error(f"AI service error finding similar emails: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': ERROR_MESSAGES['ai_service_error'],
                'details': str(e)
            }, status=HTTP_STATUS['bad_gateway'])
            
    except Exception as e:
        logger.error(f"Unexpected error finding similar emails: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:serve_login')
def suggest_reply(request: HttpRequest, email_id: str) -> JsonResponse:
    """API endpoint to generate an AI-suggested reply for an email.
    
    Args:
        request: The HTTP request object containing context data
        email_id: ID of the email to generate reply for
        
    Returns:
        JSON response with suggested reply text
        
    Raises:
        Email.DoesNotExist: If email_id is not found
        AIServiceError: If reply generation fails
        ValidationError: If request data is invalid
    """
    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': ERROR_MESSAGES['invalid_request'],
                'details': 'Invalid JSON format in request body'
            }, status=HTTP_STATUS['bad_request'])
        
        # Generate reply suggestion
        recommendations = recommendation_service.generate_recommendations(
            data.get('content', ''),
            data.get('subject', ''),
            data.get('sender', '')
        )
        
        return JsonResponse({
            'success': True,
            'reply': recommendations.get('reply_template', '')
        })
    except Exception as e:
        logger.error(f"Error suggesting reply: {str(e)}")
        return JsonResponse({
            'error': f'Failed to suggest reply: {str(e)}'
        }, status=500)

@require_GET
@login_required(login_url='email_app:serve_login')
def daily_summary(request: HttpRequest):
    """API endpoint to get a summary of the day's emails
    
    Args:
        request: HTTP request
        
    Returns:
        JsonResponse with daily summary
    """
    try:
        # Get date parameter (optional)
        from datetime import datetime, timedelta
        date_str = request.GET.get('date', None)
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=400)
        else:
            date = datetime.now().date()
        
        # Get emails for the date
        from email_app.models import Email
        emails = Email.objects.filter(
            date__date=date, 
            folder='INBOX'
        ).values('id', 'subject', 'sender', 'date', 'snippet', 'body')
        
        # Convert QuerySet to list
        email_list = list(emails)
        
        # Generate summaries for each email
        summaries = []
        for email in email_list:
            result = summarization_service.summarize_email({
                'content': email.get('body', ''),
                'subject': email.get('subject', ''),
                'sender': email.get('sender', '')
            })
            summaries.append({
                'id': email.get('id'),
                'subject': email.get('subject'),
                'summary': result.get('summary', ''),
                'priority': result.get('priority', 'Medium'),
                'category': result.get('category', 'General')
            })
        
        # Group by category
        categories = {}
        for summary in summaries:
            category = summary['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(summary)
        
        # Generate action items
        action_items = []
        for summary in summaries:
            if summary['priority'] == 'High':
                action_items.append(f"Review {summary['subject']} - marked as high priority")
        
        return JsonResponse({
            'success': True,
            'date': date.strftime('%Y-%m-%d'),
            'total_emails': len(summaries),
            'categories': categories,
            'action_items': action_items
        })
    except Exception as e:
        logger.error(f"Error generating daily summary: {str(e)}")
        return JsonResponse({
            'error': f'Failed to generate daily summary: {str(e)}'
        }, status=500)
