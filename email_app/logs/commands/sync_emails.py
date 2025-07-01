import psycopg2
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from email_app.GMAIL_API.gmail_auth import GmailAuth
from email_app.GMAIL_API.gmail_api import GmailAPI
from email_app.models import Email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from email.utils import parsedate_to_datetime, parseaddr
import pytz
from email_app.ai_services.prioritazation.prioritization_service import EmailPrioritizationService
from email_app.ai_services import EmailCategorizationService

console = Console()

class Command(BaseCommand):
    help = 'Sync emails from Gmail and show the process in terminal'

    def __init__(self):
        super().__init__()
        self.db_params = {
            'dbname': 'email_db',
            'user': 'postgres',
            'password': 'email1234',
            'host': 'localhost',
            'port': '5432'
        }
        # Initialize models
        self.priority_service = EmailPrioritizationService()
        self.categorization_service = EmailCategorizationService()

    def parse_recipients(self, headers):
        """Extract recipients from email headers."""
        to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
        cc_header = next((h['value'] for h in headers if h['name'].lower() == 'cc'), '')
        bcc_header = next((h['value'] for h in headers if h['name'].lower() == 'bcc'), '')
        
        recipients = []
        for header in [to_header, cc_header, bcc_header]:
            if header:
                parts = header.split(',')
                for part in parts:
                    name, email = parseaddr(part.strip())
                    if email:
                        recipients.append(email)
        return recipients

    def extract_attachments(self, payload):
        """Extract attachment information from message payload."""
        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part.get('body', {}).get('size', 0)
                    })
        return attachments

    def handle(self, *args, **options):
        try:
            # Initialize GmailAuth
            console.print("\n[bold blue]Initializing Gmail Authentication...[/bold blue]")
            gmail_auth = GmailAuth()
            credentials = gmail_auth.get_credentials()

            if not credentials:
                console.print("[red]No valid credentials found. Please authenticate first.[/red]")
                return

            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get user profile
            user_info = service.users().getProfile(userId='me').execute()
            user_email = user_info['emailAddress']
            
            console.print(f"\n[green]✓ Connected to Gmail account:[/green] {user_email}")
            
            # Create a table for displaying emails
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Status", style="bold")
            table.add_column("Subject", style="cyan")
            table.add_column("From", style="green")
            table.add_column("Date", style="yellow")
            table.add_column("Category", style="blue")
            table.add_column("Priority", style="red")

            # Connect to database
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()
            
            # List messages
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Fetching emails from Gmail...", total=None)
                results = service.users().messages().list(userId='me', maxResults=10).execute()
                messages = results.get('messages', [])

            if not messages:
                console.print("[red]No emails found.[/red]")
                return

            console.print(f"\n[yellow]Processing {len(messages)} emails...[/yellow]")

            for idx, message in enumerate(messages, 1):
                try:
                    console.print(f"\n[cyan]Processing email {idx}/{len(messages)}[/cyan]")
                    
                    # Get message details
                    msg = service.users().messages().get(userId='me', id=message['id']).execute()
                    
                    # Process headers
                    headers = msg['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    sender_name, sender_email = parseaddr(sender)
                    date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                    
                    # Parse date
                    try:
                        date = parsedate_to_datetime(date_str)
                        if date.tzinfo is None:
                            date = pytz.UTC.localize(date)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not parse date '{date_str}'. Using current time.[/yellow]")
                        date = datetime.now(pytz.UTC)

                    # Get message details
                    snippet = msg.get('snippet', '')
                    labels = msg.get('labelIds', [])
                    recipients = self.parse_recipients(headers)
                    recipients_json = json.dumps(recipients)
                    attachments = self.extract_attachments(msg['payload'])
                    has_attachments = bool(attachments)
                    
                    # Determine folder
                    folder = 'INBOX'
                    if 'SENT' in labels:
                        folder = 'SENT'
                    elif 'DRAFT' in labels:
                        folder = 'DRAFT'
                    elif 'SPAM' in labels:
                        folder = 'SPAM'
                    elif 'TRASH' in labels:
                        folder = 'TRASH'

                    # Predict category using the service first
                    category_result = self.categorization_service.categorize_email({
                        'subject': subject,
                        'content': snippet,
                        'sender': sender,
                        'recipients': recipients_json
                    })
                    category = category_result['category']
                    category_confidence = category_result['confidence']

                    # Predict priority using the service with the category
                    priority, priority_scores, priority_explanation = self.priority_service.predict_priority(
                        subject=subject,
                        body=snippet,
                        sender=sender_email,
                        category=category  # Pass the category we just got
                    )
                    priority_score = max(priority_scores.values())

                    # Insert or update in database
                    cur.execute("""
                        INSERT INTO emails (
                            id, user_email, subject, sender, recipients, date, snippet,
                            has_attachments, attachments, star, label, folder, last_modified,
                            priority, priority_score, priority_explanation, priority_last_updated,
                            category, category_confidence, category_last_updated
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(),
                            %s, %s, %s, NOW(), %s, %s, NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            subject = EXCLUDED.subject,
                            sender = EXCLUDED.sender,
                            recipients = EXCLUDED.recipients,
                            date = EXCLUDED.date,
                            snippet = EXCLUDED.snippet,
                            has_attachments = EXCLUDED.has_attachments,
                            attachments = EXCLUDED.attachments,
                            star = EXCLUDED.star,
                            label = EXCLUDED.label,
                            folder = EXCLUDED.folder,
                            last_modified = NOW(),
                            priority = EXCLUDED.priority,
                            priority_score = EXCLUDED.priority_score,
                            priority_explanation = EXCLUDED.priority_explanation,
                            priority_last_updated = NOW(),
                            category = EXCLUDED.category,
                            category_confidence = EXCLUDED.category_confidence,
                            category_last_updated = NOW()
                        RETURNING (xmax = 0)::boolean as inserted;
                    """, (
                        message['id'], user_email, subject, sender_email,
                        recipients_json, date, snippet, has_attachments,
                        json.dumps(attachments), 'STARRED' in labels,
                        ','.join(labels), folder,
                        priority, priority_score, priority_explanation,
                        category, category_confidence
                    ))
                    
                    inserted = cur.fetchone()[0]
                    conn.commit()

                    # Add to display table
                    status = "[green]✓ New[/green]" if inserted else "[blue]↻ Updated[/blue]"
                    table.add_row(
                        status,
                        (subject[:47] + '...') if len(subject) > 50 else subject,
                        (sender[:27] + '...') if len(sender) > 30 else sender,
                        date.strftime('%Y-%m-%d %H:%M'),
                        f"{category} ({category_confidence:.2f})",
                        f"{priority} ({priority_score:.2f})"
                    )

                except Exception as e:
                    conn.rollback()
                    console.print(f"[red]Error processing message {message['id']}: {str(e)}[/red]")
                    continue

            # Display results
            console.print("\n[bold green]Email Sync Results:[/bold green]")
            console.print(table)

            # Display summary
            cur.execute("SELECT COUNT(*) FROM emails")
            total_emails = cur.fetchone()[0]
            console.print(f"\n[green]Total emails in database:[/green] {total_emails}")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close() 