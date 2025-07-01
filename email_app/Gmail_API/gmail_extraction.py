from .google_apis import create_service
import base64
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil import parser
import json
from email_app.ai_services import EmailCategorizationService

client_secret_file = 'C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/email_app/GMAIL_API/credentials.json'
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']
service = create_service(client_secret_file,API_SERVICE_NAME,API_VERSION,SCOPES)

# Initialize the categorization service
categorizer = EmailCategorizationService()

def process_message(msg):
    """Process a Gmail message and extract relevant information"""
    try:
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
        body = get_email_body(msg['payload'])
        snippet = msg.get('snippet', '')
        if not body and not snippet:
            print(f"Warning: Empty body and snippet for message {msg['id']}")
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

        # Create email data dictionary
        email_dict = {
            'id': msg['id'],
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
            'priority': None,
            'priority_score': None,
            'priority_explanation': None,
            'priority_last_updated': None,
            'category': None,
            'category_confidence': None,
            'category_last_updated': None
        }

        # Auto-categorize the email using the BERT hybrid model
        try:
            categorization_result = categorizer.categorize_email({
                'subject': subject,
                'content': body,
                'sender': sender,
                'recipients': recipients
            })
            
            email_dict['category'] = categorization_result['category']
            email_dict['category_confidence'] = categorization_result['confidence']
            email_dict['category_last_updated'] = datetime.now(timezone.utc)
            
            print(f"Categorized email {msg['id']} as {categorization_result['category']} with confidence {categorization_result['confidence']}")
        except Exception as e:
            print(f"Error categorizing email {msg['id']}: {str(e)}")

        return email_dict

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return None

def get_email_body(payload):
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
                    html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    return soup.get_text()
            elif 'parts' in part:
                body = get_email_body(part)
                if body:
                    return body
    
    return ''

def extract_emails(service, query=''):
    """Extract emails from Gmail with pagination support"""
    try:
        email_data = []
        next_page_token = None
        total_processed = 0
        
        while True:
            # List messages with pagination
            results = service.users().messages().list(
                userId='me',
                q=query,
                pageToken=next_page_token
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                break
                
            print(f"Processing {len(messages)} messages in current page")
            
            for message in messages:
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Process message and add to email_data
                    processed_message = process_message(msg)
                    if processed_message:
                        email_data.append(processed_message)
                        total_processed += 1
                        
                        if total_processed % 10 == 0:
                            print(f"Processed {total_processed} messages")
                    else:
                        print(f"Warning: Failed to process message {message['id']}")
                        
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    continue
            
            # Check for more pages
            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                break
                
        print(f"\nEmail extraction complete:")
        print(f"Total messages processed: {total_processed}")
        return email_data
        
    except Exception as e:
        print(f"Error in extract_emails: {str(e)}")
        return []