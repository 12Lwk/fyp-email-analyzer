import json
import logging
from typing import Dict, Any, Optional, TypedDict, Union
from base64 import b64decode
from django.utils import timezone

from django.http import HttpResponse, JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from ..utils.constants import ERROR_MESSAGES, HTTP_STATUS
from ..voice_services.tts_service import TextToSpeechService
from ..voice_services.stt_service import SpeechToTextService
from ..voice_services.exceptions import TTSError, STTError, AudioProcessingError
from ..voice_services.voice_utils import AudioProcessor
from ..ai_services.llm.llm_service import LLMService
from ..ai_services.exceptions import AIServiceError
from ..models import Email
from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from google.oauth2 import service_account
import os

logger = logging.getLogger(__name__)

# Type definitions
class IntentData(TypedDict):
    intent: str
    parameters: Dict[str, Any]
    confidence: float

class VoiceCommandResponse(TypedDict):
    success: bool
    transcription: str
    intent: str
    parameters: Dict[str, Any]
    confidence: float
    response_text: str

# Initialize Gemini-based LLM service
llm_service = LLMService()

# Initialize Google Cloud clients
def get_speech_client():
    try:
        # Use the existing demo_speech_to_text_account.json file
        credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'voice_services', 
            'demo_speech_to_text_account.json'
        )
        
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return speech_v1.SpeechClient(credentials=credentials)
        else:
            logger.warning(f"Speech-to-text credentials file not found at: {credentials_path}")
            # Fall back to using the TextToSpeechService class which should have its own authentication
            return None
    except Exception as e:
        logger.warning(f"Could not initialize Google Cloud Speech client: {str(e)}")
        return None

def get_tts_client():
    try:
        # Use the existing demo_text_to_speech_account.json file
        credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'voice_services', 
            'demo_text_to_speech_account.json'
        )
        
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return texttospeech_v1.TextToSpeechClient(credentials=credentials)
        else:
            logger.warning(f"Text-to-speech credentials file not found at: {credentials_path}")
            # Fall back to using the TextToSpeechService class which should have its own authentication
            return None
    except Exception as e:
        logger.warning(f"Could not initialize Google Cloud Text-to-Speech client: {str(e)}")
        return None

class CommandProcessor:
    """Processes voice commands using LLM for intent extraction and response generation."""
    
    def __init__(self) -> None:
        self.llm_service = llm_service
    
    def extract_intent(self, text: str) -> IntentData:
        """Extract intent from text using Gemini model.
        
        Args:
            text: The transcribed voice command text
            
        Returns:
            Dictionary containing intent, parameters, and confidence
            
        Raises:
            AIServiceError: If intent extraction fails
        """
        try:
            prompt = f"""Analyze the following voice command and extract the intent and parameters:
            Command: {text}
            
            Return a JSON with:
            - intent: The main action (e.g., read_email, compose_email, search_emails)
            - parameters: Any relevant parameters (e.g., recipient, subject, content)
            - confidence: Confidence score between 0 and 1
            """
            
            response = self.llm_service.generate_response(prompt)
            return json.loads(response)
            
        except (json.JSONDecodeError, AIServiceError) as e:
            logger.error(f"Error extracting intent: {str(e)}", exc_info=True)
            return {
                'intent': 'unknown',
                'parameters': {},
                'confidence': 0.0
            }
    
    def generate_response(self, intent_data: IntentData) -> str:
        """Generate natural language response using Gemini model.
        
        Args:
            intent_data: Dictionary containing intent information
            
        Returns:
            Natural language response string
            
        Raises:
            AIServiceError: If response generation fails
        """
        try:
            prompt = f"""Generate a natural language response for the following voice command intent:
            Intent: {intent_data['intent']}
            Parameters: {json.dumps(intent_data['parameters'])}
            Confidence: {intent_data['confidence']}
            
            Return a concise, natural-sounding response confirming the action taken.
            """
            
            return self.llm_service.generate_response(prompt)
            
        except AIServiceError as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "I'll process that command for you."

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def text_to_speech(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """API endpoint to convert text to speech.
    
    Args:
        request: The HTTP request object containing:
            - text: Text to convert to speech
            - voice: Optional voice name (default: en-US-Standard-C)
            - language: Optional language code (default: en-US)
        
    Returns:
        HTTP response with audio data or error message
        
    Raises:
        TTSError: If text-to-speech conversion fails
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
        
        text = data.get('text', '')
        voice_name = data.get('voice', 'en-US-Standard-C')
        language_code = data.get('language', 'en-US')
        
        if not text:
            raise ValidationError('Text is required for text-to-speech conversion')
        
        # Initialize TTS service and convert text
        try:
            tts_service = TextToSpeechService()
            audio_content = tts_service.text_to_speech(text, voice_name, language_code)
            
            # Return audio response
            response = HttpResponse(audio_content, content_type='audio/mp3')
            response['Content-Disposition'] = 'inline; filename="speech.mp3"'
            return response
            
        except TTSError as e:
            logger.error(f"TTS service error: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': ERROR_MESSAGES['tts_error'],
                'details': str(e)
            }, status=HTTP_STATUS['bad_gateway'])
            
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Unexpected error in text-to-speech endpoint: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
def speech_to_text(request):
    """Convert speech to text using Google Cloud Speech-to-Text API."""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format in request body'
            }, status=400)
            
        if 'audio' not in data:
            return JsonResponse({
                'success': False,
                'error': 'No audio data provided in request'
            }, status=400)
            
        try:
            audio_data = b64decode(data.get('audio'))
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error decoding base64 audio: {str(e)}'
            }, status=400)
        
        # Try using Google Cloud Speech-to-Text
        client = get_speech_client()
        if client:
            try:
                # Configure audio
                audio = speech_v1.RecognitionAudio(content=audio_data)
                config = speech_v1.RecognitionConfig(
                    encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    model="command_and_search",  # Using command model which is better for short phrases
                    use_enhanced=True,  # Use enhanced model
                    speech_contexts=[{
                        "phrases": ["read", "email", "reply", "forward", "analyze", "important", "mark"],
                        "boost": 15.0
                    }]
                )
                
                # Perform speech recognition
                logger.info("Sending audio to Google Cloud Speech-to-Text API")
                response = client.recognize(config=config, audio=audio)
                
                # Extract transcription
                transcription = ""
                for result in response.results:
                    transcription += result.alternatives[0].transcript
                
                logger.info(f"Transcription result: '{transcription}'")
                
                if not transcription:
                    return JsonResponse({
                        'success': False,
                        'error': 'No speech detected in audio',
                        'details': 'The audio was processed successfully, but no speech was detected.'
                    }, status=200)
                    
                return JsonResponse({
                    'success': True,
                    'transcription': transcription,
                    'text': transcription  # Adding both keys for compatibility
                })
                
            except Exception as e:
                logger.error(f"Google Cloud Speech-to-Text API error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Google Cloud Speech API error: {str(e)}',
                    'details': 'There was an error processing your audio with Google Cloud. Falling back to alternative method.'
                }, status=500)
        else:
            # Fall back to SpeechToTextService
            try:
                logger.info("Falling back to SpeechToTextService")
                stt_service = SpeechToTextService()
                transcription = stt_service.transcribe_audio_data(audio_data)
                
                if not transcription:
                    return JsonResponse({
                        'success': False,
                        'error': 'No speech detected in audio',
                        'details': 'The audio was processed successfully, but no speech was detected.'
                    }, status=200)
                    
                return JsonResponse({
                    'success': True,
                    'transcription': transcription,
                    'text': transcription  # Adding both keys for compatibility
                })
            except Exception as e:
                logger.error(f"SpeechToTextService error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Speech-to-text service error: {str(e)}',
                    'details': 'Cannot process audio with any available service.'
                }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in speech_to_text: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error processing speech: {str(e)}',
            'details': 'An unexpected error occurred while processing your request.'
        }, status=500)

@csrf_exempt
@require_POST
def text_to_speech(request):
    """Convert text to speech using Google Cloud Text-to-Speech API."""
    try:
        # Skip login check for now for testing purposes
        # if not request.user.is_authenticated:
        #     return JsonResponse({
        #         'success': False,
        #         'error': 'Authentication required'
        #     }, status=401)
            
        data = json.loads(request.body)
        text = data.get('text')
        
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'No text provided'
            }, status=400)
        
        # Try using Google Cloud Text-to-Speech
        client = get_tts_client()
        if client:
            # Configure synthesis input
            synthesis_input = texttospeech_v1.SynthesisInput(text=text)
            
            # Configure voice
            voice = texttospeech_v1.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Standard-C",
                ssml_gender=texttospeech_v1.SsmlVoiceGender.FEMALE,
            )
            
            # Configure audio
            audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.MP3
            )
            
            # Perform text-to-speech
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Return audio content
            audio_content = response.audio_content
        else:
            # Fall back to TextToSpeechService
            tts_service = TextToSpeechService()
            audio_content = tts_service.text_to_speech(
                text, 
                voice_name="en-US-Standard-C", 
                language_code="en-US"
            )
        
        # Return audio response
        return HttpResponse(
            audio_content,
            content_type='audio/mp3'
        )
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def process_voice_command(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """API endpoint to process a voice command using Gemini for NLU."""
    try:
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to use voice command")
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'redirect': '/login/'  # Provide redirect URL
            }, status=401)

        # Get and process audio data
        content_type = request.content_type
        audio_data: Optional[bytes] = None
        language_code = 'en-US'
        return_audio = False
        voice_name = 'en-US-Standard-C'
        
        if 'application/json' in content_type:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': ERROR_MESSAGES['invalid_request'],
                    'details': 'Invalid JSON format in request body'
                }, status=HTTP_STATUS['bad_request'])
            
            base64_audio = data.get('audio', '')
            language_code = data.get('language', 'en-US')
            return_audio = data.get('return_audio', False)
            voice_name = data.get('voice', 'en-US-Standard-C')
            
            if not base64_audio:
                return JsonResponse({
                    'success': False,
                    'error': 'Audio data is required',
                    'use_browser': True  # Suggest using browser-based speech recognition
                }, status=HTTP_STATUS['bad_request'])
            
            try:
                audio_processor = AudioProcessor()
                audio_data = audio_processor.decode_base64_audio(base64_audio)
                
                audio_format = data.get('format', 'wav')
                if audio_format != 'wav':
                    audio_data = audio_processor.convert_audio_format(audio_data, audio_format, 'wav')
            except AudioProcessingError as e:
                logger.error(f"Audio processing error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': ERROR_MESSAGES['audio_processing_error'],
                    'details': str(e),
                    'use_browser': True  # Suggest using browser-based speech recognition
                }, status=HTTP_STATUS['bad_request'])
        else:
            audio_data = request.body
            language_code = request.GET.get('language', 'en-US')
            return_audio = False
        
        if not audio_data:
            return JsonResponse({
                'success': False,
                'error': 'No audio data provided',
                'use_browser': True  # Suggest using browser-based speech recognition
            }, status=HTTP_STATUS['bad_request'])
        
        # Convert speech to text
        try:
            stt_service = SpeechToTextService()
            transcription = stt_service.transcribe_audio_data(audio_data, language_code)
            
            if not transcription:
                return JsonResponse({
                    'success': False,
                    'error': 'Could not transcribe audio. Please try speaking more clearly.',
                    'use_browser': True  # Suggest using browser-based speech recognition
                }, status=HTTP_STATUS['bad_request'])
        except STTError as e:
            logger.error(f"STT service error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f"Speech-to-text error: {str(e)}",
                'details': "Service issue with speech recognition. Try browser speech recognition instead.",
                'use_browser': True  # Suggest using browser-based speech recognition
            }, status=HTTP_STATUS['bad_gateway'])
        
        # Process command
        try:
            command_processor = CommandProcessor()
            intent_data = command_processor.extract_intent(transcription)
            response_text = command_processor.generate_response(intent_data)
            
            # Convert response to speech if requested
            if return_audio:
                try:
                    tts_service = TextToSpeechService()
                    audio_response = tts_service.text_to_speech(
                        response_text,
                        voice_name=voice_name,
                        language_code=language_code
                    )
                    
                    response = HttpResponse(audio_response, content_type='audio/mp3')
                    response['Content-Disposition'] = 'inline; filename="response.mp3"'
                    return response
                except TTSError as e:
                    logger.error(f"TTS service error: {str(e)}", exc_info=True)
                    return JsonResponse({
                        'success': False,
                        'error': ERROR_MESSAGES['tts_error'],
                        'details': str(e),
                        'use_browser': True,  # Suggest using browser-based TTS
                        'text_response': response_text  # Include text for browser TTS
                    }, status=HTTP_STATUS['bad_gateway'])
            
            # Return text response
            response_data: VoiceCommandResponse = {
                'success': True,
                'transcription': transcription,
                'intent': intent_data['intent'],
                'parameters': intent_data['parameters'],
                'confidence': intent_data['confidence'],
                'response_text': response_text
            }
            
            return JsonResponse(response_data)
            
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': "AI service error: Could not process your command.",
                'details': str(e),
                'use_browser': True  # Suggest using browser-based processing
            }, status=HTTP_STATUS['bad_gateway'])
            
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e),
            'use_browser': True  # Suggest using browser-based processing
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Unexpected error processing voice command: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': "An unexpected error occurred. Please try browser-based voice recognition instead.",
            'details': str(e),
            'use_browser': True  # Suggest using browser-based processing
        }, status=HTTP_STATUS['server_error'])

@require_GET
@login_required(login_url='email_app:login')
def available_voices(request: HttpRequest) -> JsonResponse:
    """API endpoint to get available TTS voices.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JSON response with list of available voices or error message
        
    Raises:
        TTSError: If fetching voices fails
    """
    try:
        # Initialize TTS service and get voices
        try:
            tts_service = TextToSpeechService()
            voices = tts_service.get_available_voices()
            
            return JsonResponse({
                'success': True,
                'voices': voices
            })
        except TTSError as e:
            logger.error(f"TTS service error getting voices: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': ERROR_MESSAGES['tts_error'],
                'details': str(e)
            }, status=HTTP_STATUS['bad_gateway'])
            
    except Exception as e:
        logger.error(f"Unexpected error getting available voices: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def read_email(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """API endpoint to read an email aloud using text-to-speech.
    
    Args:
        request: The HTTP request object containing:
            - email_id: ID of the email to read
            - voice: Optional voice name (default: en-US-Standard-C)
            - language: Optional language code (default: en-US)
        
    Returns:
        HTTP response with audio data or JSON response with content for client-side TTS
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
        
        email_id = data.get('email_id')
        voice_name = data.get('voice', 'en-US-Standard-C')
        language_code = data.get('language', 'en-US')
        return_text = data.get('return_text', False)
        
        if not email_id:
            raise ValidationError('Email ID is required')
        
        # Get the email from the database
        try:
            email = Email.objects.get(id=email_id)
        except Email.DoesNotExist:
            logger.warning(f"Email with ID {email_id} not found")
            return JsonResponse({
                'error': 'Email not found',
                'details': f'No email found with ID: {email_id}'
            }, status=HTTP_STATUS['not_found'])
        
        # Format text for reading
        subject = email.subject or 'No subject'
        email_content = email.snippet or 'No content'
        text_to_read = f"Subject: {subject}\n\n{email_content}"
        
        # If client requested text only, return it
        if return_text:
            return JsonResponse({
                'success': True,
                'content': text_to_read
            })
        
        # Initialize TTS service and convert text
        try:
            # First try with Google Cloud
            client = get_tts_client()
            if client:
                synthesis_input = texttospeech_v1.SynthesisInput(text=text_to_read)
                voice = texttospeech_v1.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name,
                    ssml_gender=texttospeech_v1.SsmlVoiceGender.FEMALE,
                )
                audio_config = texttospeech_v1.AudioConfig(
                    audio_encoding=texttospeech_v1.AudioEncoding.MP3
                )
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                audio_content = response.audio_content
            else:
                # Fall back to TextToSpeechService
                tts_service = TextToSpeechService()
                audio_content = tts_service.text_to_speech(text_to_read, voice_name, language_code)
            
            # Return audio response
            response = HttpResponse(audio_content, content_type='audio/mp3')
            response['Content-Disposition'] = 'inline; filename="email-reading.mp3"'
            return response
            
        except Exception as e:
            logger.error(f"Error in TTS service: {str(e)}", exc_info=True)
            
            # If TTS fails, return text content that client can use with browser's TTS
            return JsonResponse({
                'success': False,
                'error': str(e),
                'fallback': True,
                'content': text_to_read
            })
            
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Unexpected error reading email: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def process_reply(request: HttpRequest) -> JsonResponse:
    """Process a voice reply to an email.
    
    Args:
        request: The HTTP request object containing:
            - audio: Base64 encoded audio data
            - email_id: ID of the email being replied to
            
    Returns:
        JSON response with success status and message
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        base64_audio = data.get('audio', '')
        email_id = data.get('email_id')
        
        if not base64_audio or not email_id:
            raise ValidationError('Audio data and email ID are required')
        
        # Convert audio to text
        audio_processor = AudioProcessor()
        audio_data = audio_processor.decode_base64_audio(base64_audio)
        
        stt_service = SpeechToTextService()
        reply_text = stt_service.transcribe_audio_data(audio_data)
        
        if not reply_text:
            raise ValidationError('Could not transcribe reply')
        
        # Get the original email
        email = Email.objects.get(id=email_id)
        
        # Create reply email
        reply = Email(
            user_email=request.user.email,
            subject=f"Re: {email.subject}",
            sender=request.user.email,
            recipients=email.sender,
            content=reply_text,
            date=timezone.now()
        )
        reply.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Reply sent successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Error processing reply: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def process_forward(request: HttpRequest) -> JsonResponse:
    """Process a voice forward command.
    
    Args:
        request: The HTTP request object containing:
            - audio: Base64 encoded audio data with recipient email
            - email_id: ID of the email to forward
            
    Returns:
        JSON response with success status and message
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        base64_audio = data.get('audio', '')
        email_id = data.get('email_id')
        
        if not base64_audio or not email_id:
            raise ValidationError('Audio data and email ID are required')
        
        # Convert audio to text
        audio_processor = AudioProcessor()
        audio_data = audio_processor.decode_base64_audio(base64_audio)
        
        stt_service = SpeechToTextService()
        recipient_text = stt_service.transcribe_audio_data(audio_data)
        
        if not recipient_text:
            raise ValidationError('Could not transcribe recipient email')
        
        # Extract email address from transcribed text
        # This is a simple implementation - you might want to improve it
        recipient_email = recipient_text.strip().lower()
        
        # Get the original email
        email = Email.objects.get(id=email_id)
        
        # Create forward email
        forward = Email(
            user_email=request.user.email,
            subject=f"Fwd: {email.subject}",
            sender=request.user.email,
            recipients=recipient_email,
            content=f"Forwarded message:\n\n{email.content}",
            date=timezone.now()
        )
        forward.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Email forwarded successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Error processing forward: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])

@csrf_exempt
@require_POST
@login_required(login_url='email_app:login')
def process_compose(request: HttpRequest) -> JsonResponse:
    """Process a voice compose command.
    
    Args:
        request: The HTTP request object containing:
            - audio: Base64 encoded audio data with email content
            
    Returns:
        JSON response with success status and message
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        base64_audio = data.get('audio', '')
        
        if not base64_audio:
            raise ValidationError('Audio data is required')
        
        # Convert audio to text
        audio_processor = AudioProcessor()
        audio_data = audio_processor.decode_base64_audio(base64_audio)
        
        stt_service = SpeechToTextService()
        email_text = stt_service.transcribe_audio_data(audio_data)
        
        if not email_text:
            raise ValidationError('Could not transcribe email content')
        
        # Use LLM to extract recipient and subject
        prompt = f"""Extract the recipient email and subject from the following email content:
        {email_text}
        
        Return a JSON with:
        - recipient: The recipient's email address
        - subject: The email subject
        - content: The email content
        """
        
        llm_response = llm_service.generate_response(prompt)
        email_data = json.loads(llm_response)
        
        # Create new email
        email = Email(
            user_email=request.user.email,
            subject=email_data.get('subject', 'No Subject'),
            sender=request.user.email,
            recipients=email_data.get('recipient', ''),
            content=email_data.get('content', email_text),
            date=timezone.now()
        )
        email.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Email sent successfully'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'error': ERROR_MESSAGES['invalid_request'],
            'details': str(e)
        }, status=HTTP_STATUS['bad_request'])
    except Exception as e:
        logger.error(f"Error processing compose: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': ERROR_MESSAGES['processing_error']
        }, status=HTTP_STATUS['server_error'])
