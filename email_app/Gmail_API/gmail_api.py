import os
import base64
import html
import ssl
import socket
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from .google_apis import create_service
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from urllib3.util.retry import Retry
from datetime import datetime, timezone
import json
import logging
import traceback
import pandas as pd
import dateutil.parser as parser

logger = logging.getLogger(__name__)

class CustomHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            ssl_version=ssl.PROTOCOL_TLS,
            ciphers='DEFAULT@SECLEVEL=1'
        )
        context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class GmailAPI:
    """Simple Gmail API wrapper class"""
    
    def __init__(self, credentials=None):
        """Initialize Gmail API service"""
        try:
            if not credentials:
                raise ValueError("Credentials are required to initialize Gmail service")
                
            # Create service directly with credentials
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {str(e)}")
            raise Exception(f"Failed to initialize Gmail service: {str(e)}")
    
    def get_user_profile(self):
        """Get the user's Gmail profile"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def get_email_messages(self, query=''):
        """Get email messages for the authenticated user"""
        try:
            print("\nFetching email messages...")
            service = self.get_gmail_service()
            if not service:
                print("Failed to get Gmail service")
                return pd.DataFrame()

            # Get user profile to verify authentication
            try:
                user_profile = service.users().getProfile(userId='me').execute()
                print(f"Fetching emails for: {user_profile['emailAddress']}")
            except Exception as e:
                print(f"Failed to get user profile: {str(e)}")
                return pd.DataFrame()

            # List messages with specified query
            print(f"Searching with query: {query if query else 'all emails'}")
            
            # Process messages with pagination
            email_data = []
            next_page_token = None
            total_processed = 0
            errors = 0

            while True:
                messages_response = service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=next_page_token
                ).execute()

                messages = messages_response.get('messages', [])
                if not messages:
                    break

                total_messages = len(messages)
                print(f"Found {total_messages} messages in current page")

                print("\nProcessing messages...")
                for message in messages:
                    try:
                        msg = service.users().messages().get(
                            userId='me',
                            id=message['id'],
                            format='full'
                        ).execute()

                        # Extract headers
                        headers = msg['payload'].get('headers', [])
                        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                        date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                        to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
                        cc_header = next((h['value'] for h in headers if h['name'].lower() == 'cc'), '')

                        # Process recipients
                        recipients = []
                        if to_header:
                            recipients.extend([r.strip() for r in to_header.split(',')])
                        if cc_header:
                            recipients.extend([r.strip() for r in cc_header.split(',')])
                        recipients = list(set(recipients))  # Remove duplicates

                        # Extract body and snippet
                        body = self.get_email_body(msg['payload'])
                        snippet = msg.get('snippet', '')
                        if not body and not snippet:
                            print(f"Warning: Empty body and snippet for message {message['id']}")
                            body = ''
                            snippet = ''

                        # Process labels and folder
                        labels = msg.get('labelIds', [])
                        folder = 'INBOX'
                        if 'SENT' in labels:
                            folder = 'SENT'
                        elif 'DRAFT' in labels:
                            folder = 'DRAFT'
                        elif 'TRASH' in labels:
                            folder = 'TRASH'
                        elif 'SPAM' in labels:
                            folder = 'SPAM'

                        # Process attachments
                        attachments = []
                        if 'parts' in msg['payload']:
                            for part in msg['payload']['parts']:
                                if part.get('filename'):
                                    attachments.append({
                                        'filename': part['filename'],
                                        'mime_type': part.get('mimeType', ''),
                                        'size': int(part.get('body', {}).get('size', 0)),
                                        'attachment_id': part.get('body', {}).get('attachmentId', '')
                                    })

                        # Create email data dictionary with all required fields
                        email_dict = {
                            'id': message['id'],
                            'user_email': user_profile['emailAddress'],
                            'subject': subject,
                            'sender': sender,
                            'recipients': recipients,
                            'date': parser.parse(date_str) if date_str else datetime.now(timezone.utc),
                            'snippet': snippet,
                            'has_attachments': bool(attachments),
                            'attachments': attachments,
                            'star': 'STARRED' in labels,
                            'label': next((label for label in labels if label not in ['SENT', 'DRAFT', 'TRASH', 'SPAM', 'INBOX', 'STARRED']), ''),
                            'folder': folder,
                            'last_modified': datetime.now(timezone.utc),
                            'priority': None,  # Will be set by priority_classifier
                            'priority_score': None,
                            'priority_explanation': None,
                            'priority_last_updated': None,
                            'category': None,  # Will be set by category_model
                            'category_confidence': None,
                            'category_last_updated': None
                        }

                        email_data.append(email_dict)
                        total_processed += 1
                        
                        if total_processed % 10 == 0:
                            print(f"Processed {total_processed} messages")

                    except Exception as e:
                        print(f"Error processing message {message['id']}: {str(e)}")
                        errors += 1
                        continue

                # Check for more pages
                next_page_token = messages_response.get('nextPageToken')
                if not next_page_token:
                    break

            print(f"\nEmail processing complete:")
            print(f"Successfully processed: {total_processed}")
            print(f"Errors encountered: {errors}")

            # Convert to DataFrame
            df = pd.DataFrame(email_data)
            return df

        except Exception as e:
            print(f"Error fetching messages: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def get_email_body(self, payload):
        """Extract email body from payload"""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    body = self.get_email_body(part)
                    if body:
                        return body
        
        return ''
    
    def get_message_details(self, message_id):
        """Get details of a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract basic details
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'body': body,
                'labels': message.get('labelIds', [])
            }
        except Exception as e:
            logger.error(f"Error getting message details: {str(e)}")
            return None
    
    def _extract_body(self, payload):
        """Extract email body from payload"""
        if not payload:
            return ""
            
        body = ""
        
        def extract_part(part):
            """Recursively extract text from message parts"""
            if 'body' in part and 'data' in part['body']:
                try:
                    decoded = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    return decoded
                except Exception as e:
                    print(f"Error decoding body part: {str(e)}")
                    return ""
                    
            if 'parts' in part:
                text_parts = []
                for subpart in part['parts']:
                    if subpart.get('mimeType', '').startswith('text/'):
                        text = extract_part(subpart)
                        if text:
                            text_parts.append(text)
                return "\n".join(text_parts)
                
            return ""
            
        # First try to get plain text
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    text = extract_part(part)
                    if text:
                        body = text
                        break
            
            # If no plain text, try HTML
            if not body:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/html':
                        html = extract_part(part)
                        if html:
                            soup = BeautifulSoup(html, 'html.parser')
                            body = soup.get_text()
                            break
        
        # If no parts, try body directly
        if not body and 'body' in payload and 'data' in payload['body']:
            try:
                decoded = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                if payload.get('mimeType') == 'text/html':
                    soup = BeautifulSoup(decoded, 'html.parser')
                    body = soup.get_text()
                else:
                    body = decoded
            except Exception as e:
                print(f"Error decoding main body: {str(e)}")
        
        return body.strip()

    def _determine_folder(self, labels):
        """Determine the folder based on Gmail labels"""
        if not labels:
            return 'INBOX'
            
        folder_mapping = {
            'SENT': 'SENT',
            'DRAFT': 'DRAFT',
            'TRASH': 'TRASH',
            'SPAM': 'SPAM',
            'INBOX': 'INBOX'
        }
        
        for label in labels:
            if label in folder_mapping:
                return folder_mapping[label]
                
        return 'INBOX'  # Default to INBOX if no matching folder found

def get_email_messages(service, max_results=None):
    """Get messages from Gmail with improved error handling"""
    if not service:
        print("Gmail service not initialized")
        return []

    try:
        # Get all available labels
        labels = service.users().labels().list(userId='me').execute().get('labels', [])
        label_names = [label['name'] for label in labels]
        print(f"Found labels: {label_names}")

        # Use a set to store unique message IDs
        unique_message_ids = set()
        all_messages = []

        # If no labels specified, get all available labels
        if not label_names:
            print("No labels found")
            return []

        # Process each label
        for label_name in label_names:
            try:
                print(f"Processing label: {label_name}")
                next_page_token = None
                total_processed = 0
                
                while True:
                    # Get messages for the current label
                    results = service.users().messages().list(
                        userId='me',
                        maxResults=100,  # Fetch in batches of 100
                        pageToken=next_page_token
                    ).execute()
                    
                    messages = results.get('messages', [])
                    if not messages:
                        break
                    
                    # Add unique messages to our list
                    for message in messages:
                        if message['id'] not in unique_message_ids:
                            unique_message_ids.add(message['id'])
                            all_messages.append(message)
                            total_processed += 1
                    
                    # Check if we've reached the max_results limit
                    if max_results is not None and len(unique_message_ids) >= max_results:
                        break
                    
                    # Get the next page token
                    next_page_token = results.get('nextPageToken')
                    if not next_page_token:
                        break
                    
            except Exception as e:
                print(f"Error getting messages for label {label_name}: {str(e)}")
                continue

        print(f"Total unique messages found: {len(unique_message_ids)}")
        
        # If max_results is specified, return only that many messages
        if max_results is not None:
            return all_messages[:max_results]
        
        return all_messages

    except Exception as e:
        print(f"Error in get_email_messages: {str(e)}")
        return []

def get_message_details(service, message_id):
    """Get details of a specific message"""
    try:
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        # Extract headers
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        recipients = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

        return {
            'id': message['id'],
            'threadId': message['threadId'],
            'subject': subject,
            'from': sender,
            'to': recipients,
            'date': date,
            'snippet': message.get('snippet', ''),
            'labelIds': message.get('labelIds', [])
        }
    except Exception as e:
        print(f"Error getting message details: {str(e)}")
        return None

def save_attachment(service, message_id, attachment_id, filename):
    """Download and save an attachment"""
    try:
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()

        file_data = base64.urlsafe_b64decode(attachment['data'])
        
        # Create 'attachments' directory if it doesn't exist
        os.makedirs('attachments', exist_ok=True)
        
        # Save the file
        filepath = os.path.join('attachments', filename)
        with open(filepath, 'wb') as f:
            f.write(file_data)
            
        return filepath
    except Exception as e:
        print(f"Error saving attachment: {str(e)}")
        return None