import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import parsedate_to_datetime
from dateutil import parser
import email.utils
import re
import json
from django.db import transaction
from django.utils import timezone
import pytz
import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
import html  # Import the html module
import base64 # Ensure base64 is imported

from email_app.utils.database.db_utils import get_db_connection
from email_app.ai_services.llm.llm_service import LLMService
from email_app.ai_services.prioritazation.prioritization_service import EmailPrioritizationService
from email_app.ai_services import EmailCategorizationService
from email_app.models.email_models import EmailPriority, Email, EmailAttachment

logger = logging.getLogger(__name__)

# Initialize services
priority_service = EmailPrioritizationService()
categorization_service = EmailCategorizationService()

def parse_and_normalize_date(raw_date: Union[str, datetime, pd.Timestamp]) -> Optional[str]:
    """Parse and normalize date to UTC format.
    
    Args:
        raw_date: The date to parse (string, datetime, or pd.Timestamp)
        
    Returns:
        Normalized UTC date string or None if parsing fails
    """
    if raw_date is None:
        return None
        
    try:
        # Handle pandas Timestamp
        if isinstance(raw_date, pd.Timestamp):
            parsed_date = raw_date.to_pydatetime()
        # Handle datetime objects
        elif isinstance(raw_date, datetime):
            parsed_date = raw_date
        # Handle string inputs
        elif isinstance(raw_date, str):
            try:
                # Try email.utils parsing first for email dates
                timestamp = email.utils.mktime_tz(email.utils.parsedate_tz(raw_date))
                parsed_date = datetime.fromtimestamp(timestamp)
            except (TypeError, ValueError):
            # Fallback to dateutil parser
                parsed_date = parser.parse(raw_date)
        else:
            raise TypeError(f"Unsupported date type: {type(raw_date)}")
        
        # Ensure timezone awareness
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=pytz.UTC)
        else:
            parsed_date = parsed_date.astimezone(pytz.UTC)
            
        return parsed_date.strftime('%Y-%m-%d %H:%M:%S%z')
        
    except Exception as e:
        logger.error(f"Error in parse_and_normalize_date: {str(e)}, input: {raw_date}, type: {type(raw_date)}")
        return None

def get_body(payload: Dict[str, Any]) -> str:
    """Extracts the email body, preferring HTML over plain text."""
    body = ""
    if "parts" in payload:
        for part in payload['parts']:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    return body  # Prefer HTML body
            elif mime_type == "text/plain" and not body: # Only use plain text if HTML not found yet
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    # Convert plain text line breaks to HTML <br> tags for basic formatting
                    body = body.replace('\\r\\n', '<br>').replace('\\n', '<br>')

    # If body not found in parts, check the main payload body (for simple emails)
    if not body and 'body' in payload and 'data' in payload['body']:
         data = payload['body']['data']
         if data:
             body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
             # Check the main mimeType
             mime_type = payload.get("mimeType", "")
             if mime_type == "text/plain":
                 body = body.replace('\\r\\n', '<br>').replace('\\n', '<br>')

    return body

def process_message(message: Dict[str, Any], user_email: str) -> Optional[Dict[str, Any]]:
    """Process a Gmail message and extract relevant information."""
    try:
        if not message:
            print("Error: Empty message received")
            return None

        print("\nExtracting email data...")
        payload = message.get('payload', {}) # Get payload early

        # Initialize default values
        email_data = {
            'id': message.get('id', ''),
            'user_email': user_email,
            'subject': 'No Subject',
            'sender': '',
            'recipients': [],
            # Initially get snippet, might be overwritten by full body later
            'snippet': message.get('snippet', ''),
            'date': timezone.now(),
            'has_attachments': False,
            'attachments': [],
            'star': False,
            'label': '',
            'folder': 'INBOX',
            'last_modified': timezone.now(),
            'priority': None,
            'priority_score': None,
            'priority_explanation': None,
            'priority_last_updated': None,
            'category': None,
            'category_confidence': None,
            'category_last_updated': None
        }

        # Fetch and decode the full body
        full_body = get_body(payload)
        if full_body:
            email_data['snippet'] = html.unescape(full_body) # Store full body in snippet field and unescape
        else:
            # If body fetch failed, fallback to original snippet and unescape it
            email_data['snippet'] = html.unescape(email_data['snippet'])

        # Extract headers
        print("Processing email headers...")
        headers = {
            header['name'].lower(): header['value']
            for header in payload.get('headers', [])
            if isinstance(header, dict) and 'name' in header and 'value' in header
        }

        # Process subject
        email_data['subject'] = headers.get('subject', 'No Subject')
        email_data['subject'] = html.unescape(email_data['subject'])  # Decode HTML entities
        print(f"Subject: {email_data['subject']}")

        # Process sender
        from_header = headers.get('from', '')
        email_data['sender'] = extract_email_address(from_header)
        print(f"From: {email_data['sender']}")

        # Process recipients
        to_header = headers.get('to', '')
        cc_header = headers.get('cc', '')
        email_data['recipients'] = extract_recipients(to_header, cc_header)
        print(f"Recipients: {', '.join(email_data['recipients'])}")

        # Process date
        print("Processing date...")
        date_header = headers.get('date')
        if date_header:
            formatted_date = parse_and_normalize_date(date_header)
            if formatted_date:
                email_data['date'] = formatted_date
                print(f"Date: {formatted_date}")

        # Process attachments (using payload fetched earlier)
        print("Processing attachments...")
        attachments = process_attachments(payload)
        email_data['has_attachments'] = bool(attachments)
        email_data['attachments'] = attachments
        if attachments:
            print(f"Found {len(attachments)} attachments")

        # Process labels and folder
        print("Processing labels and folder...")
        labels = message.get('labelIds', [])
        email_data['star'] = 'STARRED' in labels
        email_data['folder'] = get_folder_from_labels(labels)
        email_data['label'] = next((label for label in labels if label not in ['SENT', 'DRAFT', 'TRASH', 'SPAM', 'INBOX', 'STARRED']), '')
        print(f"Folder: {email_data['folder']}")
        if email_data['label']:
            print(f"Label: {email_data['label']}")

        # Get category prediction first (using full body now stored in snippet)
        print("Predicting email category...")
        category_result = categorization_service.categorize_email({
            'subject': email_data['subject'],
            'content': email_data['snippet'], # Pass the full body here
            'sender': email_data['sender'],
            'recipients': email_data['recipients']
        })
        email_data['category'] = category_result['category']
        email_data['category_confidence'] = category_result['confidence']
        email_data['category_last_updated'] = timezone.now()
        print(f"Category: {email_data['category']} (Confidence: {email_data['category_confidence']:.2f})")

        # Get priority prediction using the category
        print("Predicting email priority...")
        priority_pred, priority_scores, priority_explanation = priority_service.predict_priority(
            subject=email_data['subject'],
            body=email_data['snippet'], # Pass the full body here
            sender=email_data['sender'],
            category=email_data['category']  # Now we have the category
        )
        email_data['priority'] = priority_pred
        email_data['priority_score'] = priority_scores.get(priority_pred, 0.0)
        email_data['priority_explanation'] = priority_explanation
        email_data['priority_last_updated'] = timezone.now()
        print(f"Priority: {priority_pred} (Score: {email_data['priority_score']:.2f})")

        print("Email processing completed successfully!")
        return email_data

    except Exception as e:
        logger.error(f"Error processing message {message.get('id', 'UNKNOWN')}: {str(e)}", exc_info=True) # Added logging
        print(f"Error processing message: {str(e)}") # Keep console print for immediate feedback if needed
        return None

def extract_email_address(header: str) -> str:
    """Extract email address from header string."""
    if '<' in header and '>' in header:
        return header[header.find('<')+1:header.find('>')]
    return header.strip()

def extract_recipients(to_header: str, cc_header: str) -> List[str]:
    """Extract recipient email addresses from To and CC headers."""
    recipients = []
    for header in [to_header, cc_header]:
        if header:
            for recipient in header.split(','):
                email = extract_email_address(recipient)
                if email:
                    recipients.append(email)
    return list(set(recipients))  # Remove duplicates

def process_attachments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process message attachments."""
    attachments = []
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('filename'):
                attachments.append({
                    'filename': part['filename'],
                    'mime_type': part.get('mimeType', ''),
                    'size': int(part.get('body', {}).get('size', 0)),
                    'attachment_id': part.get('body', {}).get('attachmentId', '')
                })
    return attachments

def get_folder_from_labels(labels: List[str]) -> str:
    """Determine email folder from Gmail labels."""
    if 'SENT' in labels:
        return 'SENT'
    elif 'DRAFT' in labels:
        return 'DRAFT'
    elif 'TRASH' in labels:
        return 'TRASH'
    elif 'SPAM' in labels:
        return 'SPAM'
    return 'INBOX'

@transaction.atomic
def save_email_to_db(email_data: Dict[str, Any]) -> bool:
    """Save email data to database with transaction management."""
    try:
        # Convert recipients list to JSON string
        recipients_json = json.dumps(email_data['recipients'])
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO emails (
                    id, user_email, subject, sender, recipients, date,
                    snippet, has_attachments, attachments, star, label,
                    folder, last_modified, priority, priority_score,
                    priority_explanation, priority_last_updated,
                    category, category_confidence, category_last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    last_modified = EXCLUDED.last_modified,
                    priority = EXCLUDED.priority,
                    priority_score = EXCLUDED.priority_score,
                    priority_explanation = EXCLUDED.priority_explanation,
                    priority_last_updated = EXCLUDED.priority_last_updated,
                    category = EXCLUDED.category,
                    category_confidence = EXCLUDED.category_confidence,
                    category_last_updated = EXCLUDED.category_last_updated
            """, [
                email_data['id'], email_data['user_email'], email_data['subject'],
                email_data['sender'], recipients_json,  # Use the JSON string for recipients
                email_data['date'], email_data['snippet'],
                email_data['has_attachments'], json.dumps(email_data['attachments']),
                email_data['star'], email_data['label'],
                email_data['folder'], timezone.now(),
                email_data['priority'], email_data['priority_score'],
                email_data['priority_explanation'], email_data['priority_last_updated'],
                email_data['category'], email_data['category_confidence'],
                email_data['category_last_updated']
            ])
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return False

def sync_emails(service, user_info: Dict[str, Any]) -> Tuple[int, int]:
    """Synchronize emails from Gmail to local database."""
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console = Console()
    success_count = 0
    error_count = 0
    skipped_count = 0  # Track skipped emails

    try:
        user_email = user_info.get('emailAddress')
        if not user_email:
            console.print("[red]No user email found in user info[/red]")
            return 0, 1

        console.print("\n[bold blue]Starting email sync...[/bold blue]")
        console.print(f"[green]✓ Connected to Gmail account:[/green] {user_email}")

        # Create a table for displaying emails
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Status", style="bold")
        table.add_column("Subject", style="cyan")
        table.add_column("From", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Category", style="blue")
        table.add_column("Priority", style="red")

        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        # List messages with pagination
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            task = progress.add_task(description="Fetching emails from Gmail...", total=None)
            
            try:
                next_page_token = None
                total_processed = 0
                total_emails = 0
                
                # First, get total count of messages
                console.print("\n[yellow]Counting total emails...[/yellow]")
                while True:
                    results = service.users().messages().list(
                        userId='me',
                        pageToken=next_page_token
                    ).execute()
                    
                    messages = results.get('messages', [])
                    total_emails += len(messages)
                    
                    next_page_token = results.get('nextPageToken')
                    if not next_page_token:
                        break
                
                console.print(f"\n[bold green]Total emails to process:[/bold green] {total_emails}")
                
                # Reset for processing
                next_page_token = None
                
                while True:
                    # List messages with pagination
                    results = service.users().messages().list(
                        userId='me',
                        pageToken=next_page_token
                    ).execute()
                    
                    messages = results.get('messages', [])
                    if not messages:
                        break
                        
                    console.print(f"\n[yellow]Processing {len(messages)} emails...[/yellow]")

                    for idx, message in enumerate(messages, 1):
                        try:
                            # Check if email already exists in database
                            cur.execute("""
                                SELECT id FROM emails 
                                WHERE id = %s AND user_email = %s
                            """, (message['id'], user_email))
                            
                            if cur.fetchone():
                                console.print(f"[yellow]Skipping email {idx}/{len(messages)} - already exists[/yellow]")
                                skipped_count += 1
                                continue
                            
                            console.print(f"\n[cyan]Processing email {idx}/{len(messages)} (Total: {total_processed + 1}/{total_emails})[/cyan]")
                            
                            # Get message details
                            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
                    
                            # Process message
                            email_data = process_message(msg, user_email)
                            if not email_data:
                                console.print(f"[red]Failed to process message {message['id']}[/red]")
                                error_count += 1
                                continue
                    
                            # Save to database
                            if save_email_to_db(email_data):
                                success_count += 1
                                total_processed += 1
                                # Add to display table
                                table.add_row(
                                    "[green]✓ Saved[/green]",
                                    (email_data['subject'][:47] + '...') if len(email_data['subject']) > 50 else email_data['subject'],
                                    (email_data['sender'][:27] + '...') if len(email_data['sender']) > 30 else email_data['sender'],
                                    email_data['date'].strftime('%Y-%m-%d') if isinstance(email_data['date'], datetime) else 'Unknown',
                                    f"{email_data['category']} ({email_data['category_confidence']:.2f})",
                                    f"{email_data['priority']} ({email_data['priority_score']:.2f})"
                                )
                            else:
                                error_count += 1
                                console.print(f"[red]Failed to save message {message['id']} to database[/red]")
                        
                        except Exception as e:
                            error_count += 1
                            console.print(f"[red]Error processing message: {str(e)}[/red]")
                            continue
                    
                    # Check for more pages
                    next_page_token = results.get('nextPageToken')
                    if not next_page_token:
                        break
                
                # Display results
                console.print("\n[bold green]Email Sync Results:[/bold green]")
                console.print(table)

                # Display summary with skipped count
                cur.execute("SELECT COUNT(*) FROM emails WHERE user_email = %s", (user_email,))
                total_in_db = cur.fetchone()[0]
                console.print(f"\n[green]Total emails in database:[/green] {total_in_db}")
                console.print(f"[green]Successfully synced:[/green] {success_count}")
                console.print(f"[yellow]Skipped (already exists):[/yellow] {skipped_count}")
                if error_count > 0:
                    console.print(f"[red]Failed to sync:[/red] {error_count}")
                
            except Exception as e:
                console.print(f"[red]Error fetching or processing messages: {str(e)}[/red]")
                error_count += 1

            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
                    console.print("[blue]Database connection closed[/blue]")
        
    except Exception as e:
        console.print(f"[red]Error in sync_emails: {str(e)}[/red]")
        return 0, 1 

    return success_count, error_count 