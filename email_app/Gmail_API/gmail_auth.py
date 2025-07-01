import os
import pandas as pd
import psycopg2
from datetime import datetime, timezone, timedelta
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import socket
import random
from .gmail_api import GmailAPI
import ssl
import json
import html
from email.utils import parsedate_to_datetime
import traceback
from dateutil import parser
import base64
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import certifi
from requests.adapters import Retry
from typing import Optional, Dict, Any
from django.conf import settings
import logging
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': 'email_db',
    'user': 'postgres',
    'password': 'email1234',
    'host': 'localhost',
    'port': '5432'
}

def check_gmail_auth(request) -> bool:
    """Check if the user is authenticated with Gmail.
    
    Args:
        request: The HTTP request object
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        gmail_auth = GmailAuth()
        credentials = gmail_auth.get_credentials()
        
        if not credentials:
            logger.warning("No Gmail credentials found")
            return False
            
        # Test the credentials by making a simple API call
        service = build('gmail', 'v1', credentials=credentials)
        service.users().getProfile(userId='me').execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking Gmail auth: {str(e)}", exc_info=True)
        return False

class GmailAuthError(Exception):
    """Custom exception for Gmail authentication errors."""
    pass

class GmailAuth:
    """Handles Gmail OAuth2 authentication."""
    
    def __init__(self):
        # Use absolute paths relative to the GMAIL_API directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = os.path.join(self.base_dir, 'credentials.json')
        self.token_dir = os.path.join(self.base_dir, 'token files')
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://mail.google.com/'
        ]
        self.credentials = None
        self.service = None
        self.accounts = {}
        self.current_user = None
        self.gmail_api = None
        
        # Ensure token directory exists
        if not os.path.exists(self.token_dir):
            os.makedirs(self.token_dir)
            
        # Validate credentials file exists
        if not os.path.exists(self.credentials_path):
            logger.error(f"Credentials file not found at {self.credentials_path}")
            raise GmailAuthError(f"Credentials file not found at {self.credentials_path}")
        
    def get_authorization_url(self, redirect_uri: str) -> tuple:
        """Get the authorization URL for Gmail OAuth2."""
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"Credentials file not found at {self.credentials_path}")
                raise GmailAuthError(f"Credentials file not found at {self.credentials_path}")
                
            # Create a Flow instance
            flow = Flow.from_client_secrets_file(
                self.credentials_path,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            # Generate the authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error getting authorization URL: {str(e)}", exc_info=True)
            raise GmailAuthError(f"Failed to get authorization URL: {str(e)}")
            
    def get_credentials_from_code(self, auth_code: str, redirect_uri: str) -> Credentials:
        """Exchange authorization code for credentials."""
        try:
            # Create a Flow instance
            flow = Flow.from_client_secrets_file(
                self.credentials_path,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            # Exchange auth code for credentials
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            if not credentials:
                raise GmailAuthError("Failed to obtain credentials")

            # Get user email using the credentials
            try:
                service = build('gmail', 'v1', credentials=credentials)
                user_info = service.users().getProfile(userId='me').execute()
                user_email = user_info.get('emailAddress')
                
                if not user_email:
                    raise GmailAuthError("Could not get user email from Gmail API")
                
                # Ensure token directory exists
                if not os.path.exists(self.token_dir):
                    os.makedirs(self.token_dir)
                
                # Save credentials for this user
                token_path = os.path.join(self.token_dir, f'token_{user_email}.json')
                self._save_credentials(credentials, token_path)
                
                return credentials
                
            except Exception as e:
                logger.error(f"Error getting user profile: {str(e)}", exc_info=True)
                raise GmailAuthError(f"Failed to get user profile: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error getting credentials from code: {str(e)}", exc_info=True)
            raise GmailAuthError(f"Failed to get credentials: {str(e)}")
            
    def _save_credentials(self, credentials: Credentials, token_path: str) -> None:
        """Save credentials to token file."""
        try:
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            # Ensure the token directory exists
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            
            # Save the token
            with open(token_path, 'w') as token_file:
                json.dump(token_data, token_file)
                logger.info(f"Credentials saved to {token_path}")
                
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}", exc_info=True)
            raise GmailAuthError(f"Failed to save credentials: {str(e)}")

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid user credentials from storage."""
        try:
            if not os.path.exists(self.token_dir):
                logger.info("Token directory does not exist")
                return None

            # Try to find any valid token file
            for token_file in os.listdir(self.token_dir):
                if token_file.startswith('token_'):
                    token_path = os.path.join(self.token_dir, token_file)
                    try:
                        self.credentials = Credentials.from_authorized_user_file(
                            token_path, self.scopes)
                            
                        if self.credentials and self.credentials.valid:
                            logger.info(f"Found valid credentials in {token_file}")
                            return self.credentials
                            
                        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                            logger.info("Refreshing expired credentials")
                            self.credentials.refresh(Request())
                            
                            # Save the refreshed credentials
                            with open(token_path, 'w') as token:
                                token.write(self.credentials.to_json())
                            return self.credentials
                            
                    except Exception as e:
                        logger.warning(f"Error loading credentials from {token_file}: {str(e)}")
                        continue

            logger.info("No valid credentials found")
            return None

        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}", exc_info=True)
            return None

    def get_auth_url(self) -> Dict[str, Any]:
        """Get the authorization URL for Gmail OAuth2.
        
        Returns:
            Dict containing auth URL and state
        """
        try:
            # Check if credentials file exists
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}. Please add your Google API credentials file.")
            
            flow = Flow.from_client_secrets_file(
                self.credentials_path, self.scopes)
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            return {
                'auth_url': auth_url,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Error getting auth URL: {str(e)}")
            raise

    def handle_auth_callback(self, auth_code: str) -> Optional[Credentials]:
        """Handle the OAuth2 callback and get credentials.
        
        Args:
            auth_code: Authorization code from OAuth2 callback
            
        Returns:
            Google OAuth2 credentials or None if failed
        """
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_path, self.scopes)
            flow.fetch_token(code=auth_code)
            
            self.credentials = flow.credentials
            
            # Save the credentials
            for token_file in os.listdir(self.token_dir):
                if token_file.startswith('token_'):
                    token_path = os.path.join(self.token_dir, token_file)
                    with open(token_path, 'w') as token:
                        token.write(self.credentials.to_json())
                
            return self.credentials
            
        except Exception as e:
            logger.error(f"Error handling auth callback: {str(e)}")
            return None

    def add_account(self, email):
        """Add a new account to the accounts dictionary"""
        try:
            if email in self.accounts:
                print(f"Account {email} already exists")
                return False
                
            # Try to load existing credentials for this account
            if self._load_existing_credentials(email):
                self.accounts[email] = {
                    'credentials': self.credentials,
                    'service': self.service
                }
                self.gmail_api = GmailAPI(credentials=self.credentials)
                print(f"Added existing account: {email}")
                return True
                
            # If no existing credentials, start new authentication
            if self.authenticate():
                self.accounts[self.current_user] = {
                    'credentials': self.credentials,
                    'service': self.service
                }
                self.gmail_api = GmailAPI(credentials=self.credentials)
                print(f"Added new account: {self.current_user}")
                return True
                
            return False
            
        except Exception as e:
            print(f"Error adding account {email}: {str(e)}")
            return False

    def switch_account(self, email):
        """Switch to a different account"""
        try:
            if email not in self.accounts:
                print(f"Account {email} not found")
                return False
                
            account = self.accounts[email]
            self.credentials = account['credentials']
            self.service = account['service']
            self.current_user = email
            self.gmail_api = GmailAPI(credentials=self.credentials)
            
            print(f"Switched to account: {email}")
            return True
            
        except Exception as e:
            print(f"Error switching to account {email}: {str(e)}")
            return False

    def remove_account(self, email):
        """Remove an account from the accounts dictionary"""
        try:
            if email not in self.accounts:
                print(f"Account {email} not found")
                return False
                
            # If removing current account, switch to another if available
            if self.current_user == email:
                other_accounts = [e for e in self.accounts.keys() if e != email]
                if other_accounts:
                    self.switch_account(other_accounts[0])
                else:
                    self.credentials = None
                    self.service = None
                    self.current_user = None
            
            del self.accounts[email]
            print(f"Removed account: {email}")
            return True
            
        except Exception as e:
            print(f"Error removing account {email}: {str(e)}")
            return False

    def get_available_accounts(self):
        """Get list of all available accounts"""
        return list(self.accounts.keys())

    def extract_emails(self, max_results=None):
        """Extract emails from Gmail for current account"""
        try:
            if not self.current_user:
                print("No account selected")
                return pd.DataFrame()
                
            print(f"Starting email extraction for {self.current_user}...")
            
            if not self.gmail_api:
                print("Gmail API not initialized")
                return pd.DataFrame()

            # Get messages from Gmail
            print("Fetching messages from Gmail API...")
            messages = self.gmail_api.get_email_messages(max_results=max_results)
            if not messages:
                print("No messages found in Gmail")
                return pd.DataFrame()

            print(f"Found {len(messages)} messages in Gmail")
            
            # Initialize conn as None outside the try block
            conn = None
            existing_data = None

            # Quick check for existing emails in database
            try:
                print("Checking database for existing emails...")
                conn = psycopg2.connect(**DB_CONFIG)
                with conn.cursor() as cursor:
                    # Get all existing email IDs for this user
                    cursor.execute(
                        "SELECT id FROM emails WHERE user_email = %s",
                        (self.current_user,)
                    )
                    existing_ids = {row[0] for row in cursor.fetchall()}
                    
                    # Get all current message IDs from Gmail
                    current_message_ids = {msg['id'] for msg in messages}
                    
                    # Find new emails (in Gmail but not in database)
                    new_message_ids = current_message_ids - existing_ids
                    new_count = len(new_message_ids)
                    
                    print(f"Found {new_count} new emails to process")
                    print(f"Total messages in Gmail: {len(current_message_ids)}")
                    print(f"Existing messages in DB: {len(existing_ids)}")
                    
                    if new_count == 0:
                        print("No new emails found - retrieving existing emails from database")
                        # Return existing emails from database - updated to remove 'body'
                        cursor.execute("""
                            SELECT id, subject, sender, recipients, date, snippet,
                                   has_attachments, attachments, star, label, folder
                            FROM emails 
                            WHERE user_email = %s
                            ORDER BY date DESC
                        """, (self.current_user,))
                        
                        columns = ['id', 'subject', 'sender', 'recipients', 'date', 'snippet',
                                 'has_attachments', 'attachments', 'star', 'label', 'folder']
                        existing_data = cursor.fetchall()
                        
                    # Only process new messages
                    messages = [msg for msg in messages if msg['id'] in new_message_ids]
                    
            except psycopg2.Error as db_error:
                print(f"Database connection error: {str(db_error)}")
                print("Please verify your database credentials and ensure PostgreSQL is running")
                print(f"DB Config: {DB_CONFIG}")
            except Exception as e:
                print(f"Error checking database: {str(e)}")
            finally:
                if conn:
                    conn.close()
                    print("Database connection closed")

            # If we found existing data and no new emails, return it
            if existing_data is not None and len(messages) == 0:
                print("Returning existing emails from database")
                return pd.DataFrame(existing_data, columns=columns)
            
            # Process messages
            email_data = []
            processed = 0
            failed = 0
            
            print(f"Processing {len(messages)} new messages...")
            
            for message in messages:
                try:
                    print(f"Processing message {message['id']}...")
                    result = self.process_message(message)
                    if result:
                        email_data.append(result)
                        processed += 1
                        print(f"Successfully processed message {message['id']}")
                    else:
                        failed += 1
                        print(f"Failed to process message {message['id']}")
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    failed += 1
                
                if (processed + failed) % 10 == 0:
                    print(f"Processed {processed + failed}/{len(messages)} messages")
            
            if email_data:
                df = pd.DataFrame(email_data)
                print(f"\nExtraction completed:")
                print(f"- Total messages: {len(messages)}")
                print(f"- Successfully processed: {processed}")
                print(f"- Failed to process: {failed}")
                print(f"- DataFrame shape: {df.shape}")
                print(f"- DataFrame columns: {df.columns.tolist()}")
                return df
            else:
                print("No email data could be extracted")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error in email extraction: {str(e)}")
            return pd.DataFrame()

    def save_to_csv(self, df, user_email=None):
        """Save emails to CSV with user-specific filename"""
        try:
            # Create filename with timestamp and user email
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            email_part = user_email.replace('@', '_at_').replace('.', '_') if user_email else 'unknown'
            filename = f'gmail_data_{email_part}_{timestamp}.csv'
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"Emails saved to CSV: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            return None

    def save_to_postgresql(self, df, db_config, user_email=None):
        """Save emails to PostgreSQL for specified user"""
        conn = None
        try:
            # Use current user if no email specified
            if not user_email:
                user_email = self.current_user
                if not user_email:
                    print("No user email specified")
                    return False

            print(f"\n{'='*50}")
            print("Starting database save process...")
            print(f"User email: {user_email}")
            print(f"Number of emails to process: {len(df) if df is not None else 0}")
            print(f"{'='*50}\n")

            if df is None or df.empty:
                print("No emails to save - dataframe is empty")
                return False

            print("Connecting to PostgreSQL database...")
            conn = psycopg2.connect(**db_config)
            print("Connected successfully!")

            with conn.cursor() as cursor:
                # First, ensure user profile exists
                print("Ensuring user profile exists...")
                cursor.execute("""
                    INSERT INTO email_app_userprofile (email, gmail_connected, last_sync)
                    VALUES (%s, TRUE, CURRENT_TIMESTAMP)
                    ON CONFLICT (email) DO UPDATE 
                    SET gmail_connected = TRUE, last_sync = CURRENT_TIMESTAMP
                    RETURNING id;
                """, (user_email,))
                user_profile_id = cursor.fetchone()[0]
                conn.commit()
                print(f"User profile ensured with ID: {user_profile_id}")
                
                # Get default category and priority
                print("Getting default category and priority...")
                cursor.execute("SELECT id FROM email_app_emailcategory WHERE name = 'Uncategorized' LIMIT 1")
                category_id = cursor.fetchone()
                if not category_id:
                    cursor.execute("""
                        INSERT INTO email_app_emailcategory (name, description, created_at, updated_at)
                        VALUES ('Uncategorized', 'Default category', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                    """)
                    category_id = cursor.fetchone()
                
                cursor.execute("SELECT id FROM email_app_emailpriority WHERE name = 'Medium' LIMIT 1")
                priority_id = cursor.fetchone()
                if not priority_id:
                    cursor.execute("""
                        INSERT INTO email_app_emailpriority (name, description, weight, created_at, updated_at)
                        VALUES ('Medium', 'Default priority', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                    """)
                    priority_id = cursor.fetchone()
                
                # Process emails in batches
                batch_size = 50
                total_emails = len(df)
                processed = 0
                inserted = 0
                errors = 0
                
                print(f"\nProcessing {total_emails} emails in batches of {batch_size}...")
                
                for i in range(0, total_emails, batch_size):
                    batch = df.iloc[i:i+batch_size]
                    print(f"\nProcessing batch {(i//batch_size)+1}/{(total_emails+batch_size-1)//batch_size}")
                    
                    for _, row in batch.iterrows():
                        try:
                            # Convert date string to timestamp
                            date_str = row.get('date')
                            if date_str:
                                try:
                                    if isinstance(date_str, pd.Timestamp):
                                        date = date_str.to_pydatetime()
                                    elif isinstance(date_str, datetime):
                                        date = date_str
                                    else:
                                        date = parser.parse(str(date_str))
                                        
                                    if date.tzinfo is None:
                                        date = date.replace(tzinfo=timezone.utc)
                                except Exception as e:
                                    print(f"Date parsing error for message {row.get('id', '')}: {str(e)}")
                                    date = datetime.now(timezone.utc)
                            else:
                                date = datetime.now(timezone.utc)

                            # Prepare search text
                            search_text = f"{row.get('subject', '')} {row.get('sender', '')} {row.get('snippet', '')}"
                            
                            # Insert email with proper schema alignment
                            cursor.execute("""
                                INSERT INTO emails (
                                    gmail_id, user_email, subject, sender, recipients,
                                    content, date, snippet, has_attachments, attachments,
                                    star, folder, search_text, labels,
                                    category_id, priority_id, last_modified
                                ) VALUES (
                                    %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s,
                                    %s, %s, CURRENT_TIMESTAMP
                                )
                                ON CONFLICT (gmail_id) DO UPDATE SET
                                    subject = EXCLUDED.subject,
                                    sender = EXCLUDED.sender,
                                    recipients = EXCLUDED.recipients,
                                    content = EXCLUDED.content,
                                    date = EXCLUDED.date,
                                    snippet = EXCLUDED.snippet,
                                    has_attachments = EXCLUDED.has_attachments,
                                    attachments = EXCLUDED.attachments,
                                    star = EXCLUDED.star,
                                    folder = EXCLUDED.folder,
                                    search_text = EXCLUDED.search_text,
                                    labels = EXCLUDED.labels,
                                    last_modified = CURRENT_TIMESTAMP
                                RETURNING id
                            """, (
                                row.get('id', ''),  # gmail_id
                                user_email,
                                row.get('subject', ''),
                                row.get('sender', ''),
                                json.dumps(row.get('recipients', [])),  # Convert to JSON
                                row.get('body', ''),  # content
                                date,
                                row.get('snippet', ''),
                                row.get('has_attachments', False),
                                json.dumps(row.get('attachments', [])),  # Convert to JSON
                                row.get('star', False),
                                row.get('folder', 'INBOX'),
                                search_text,
                                json.dumps(row.get('labels', [])),  # Convert to JSON
                                category_id[0] if category_id else None,
                                priority_id[0] if priority_id else None
                            ))
                            
                            email_id = cursor.fetchone()[0]

                            # Handle attachments if present
                            attachments = row.get('attachments', [])
                            if attachments:
                                for attachment in attachments:
                                    cursor.execute("""
                                        INSERT INTO email_app_emailattachment (
                                            filename, mime_type, size, attachment_id,
                                            created_at, email_id
                                        ) VALUES (
                                            %s, %s, %s, %s,
                                            CURRENT_TIMESTAMP, %s
                                        )
                                        ON CONFLICT (attachment_id) DO NOTHING
                                    """, (
                                        attachment.get('filename', ''),
                                        attachment.get('mime_type', ''),
                                        attachment.get('size', 0),
                                        attachment.get('attachment_id', ''),
                                        email_id
                                    ))

                            inserted += 1
                            processed += 1
                            
                        except Exception as e:
                            print(f"Error processing email {row.get('id', '')}: {str(e)}")
                            errors += 1
                            traceback.print_exc()
                            continue
                    
                    conn.commit()
                    print(f"Batch {(i//batch_size)+1} committed: {len(batch)} emails processed")
                    print(f"Progress: {processed}/{total_emails} ({(processed/total_emails)*100:.1f}%)")
                
                print(f"\n{'='*50}")
                print("Database update complete:")
                print(f"Total emails processed: {processed}")
                print(f"Successfully inserted/updated: {inserted}")
                print(f"Errors encountered: {errors}")
                print(f"{'='*50}\n")
                
                return True
                
        except Exception as e:
            print(f"Error saving to PostgreSQL: {str(e)}")
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
                print("Database connection closed")

    def process_message(self, message):
        """Process a single message with improved connection handling"""
        try:
            # Get full message using custom session
            full_message = self.get_message_with_session(message['id'])
            if not full_message:
                return None
            
            # Extract headers
            headers = full_message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender_raw = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            recipients_raw = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Add detailed date logging
            print(f"Processing message {message['id']}:")
            print(f"Raw date value: {date}")
            
            if not date:
                print(f"No date header found for message {message['id']}")
                # You could set a default date here
                date = datetime.now(timezone.utc).isoformat()
            
            # Parse sender and recipients
            sender_info = self._parse_email_address(sender_raw)
            recipients_info = self._parse_recipients(recipients_raw)
            
            # Extract and clean body
            body = self._extract_body(full_message.get('payload', {}))
            
            # Handle attachments
            attachments = []
            if 'parts' in full_message.get('payload', {}):
                for part in full_message['payload']['parts']:
                    if part.get('filename'):
                        filename = part['filename']
                        if filename.lower().endswith(('.pdf', '.doc', '.docx', '.csv', '.xls', '.xlsx')):
                            if 'body' in part and 'attachmentId' in part['body']:
                                try:
                                    attachment_id = part['body']['attachmentId']
                                    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}/attachments/{attachment_id}"
                                    headers = {
                                        "Authorization": f"Bearer {self.credentials.token}",
                                        "Accept": "application/json"
                                    }
                                    response = self.session.get(url, headers=headers, timeout=30)
                                    response.raise_for_status()
                                    attachment = response.json()
                                    
                                    file_data = base64.urlsafe_b64decode(attachment['data'])
                                    filepath = os.path.join('attachments', f"{message['id']}_{filename}")
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(file_data)
                                        
                                    attachments.append({
                                        'filename': filename,
                                        'path': filepath,
                                        'type': os.path.splitext(filename)[1][1:]
                                    })
                                except Exception as e:
                                    print(f"Error saving attachment: {str(e)}")
            
            # Clean text fields
            subject = self._clean_text(subject)
            body = self._clean_text(body)
            body = self._strip_html_advanced(body)
            
            # Get labels and determine folder
            labels = full_message.get('labelIds', [])
            folder = 'OTHER'
            
            # Determine folder based on labels and message properties
            if 'SENT' in labels or 'OUTBOX' in labels:
                folder = 'SENT'
            elif 'INBOX' in labels:
                folder = 'INBOX'
            elif 'SPAM' in labels:
                folder = 'SPAM'
            elif 'TRASH' in labels:
                folder = 'TRASH'
            elif 'DRAFT' in labels:
                folder = 'DRAFT'
            
            # Additional check for sent emails based on sender
            if folder == 'OTHER':
                user_email = self.get_user_email()
                if user_email and sender_raw and user_email.lower() in sender_raw.lower():
                    folder = 'SENT'
            
            # Print debug information
            print(f"Labels: {labels}")
            print(f"Sender: {sender_raw}")
            print(f"User email: {self.get_user_email()}")
            print(f"Assigned folder: {folder}")
            
            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender_raw,
                'recipients': recipients_raw,
                'body': body,
                'snippet': self._clean_text(full_message.get('snippet', '')),
                'has_attachments': bool(attachments),
                'attachments': json.dumps(attachments),
                'date': date,
                'star': 'STARRED' in labels,
                'label': ','.join(labels),
                'folder': folder
            }
        except Exception as e:
            print(f"Error processing message {message['id']}: {str(e)}")
            return None

    def get_message_with_session(self, message_id):
        """Get message using custom session"""
        try:
            url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=full"
            headers = {
                "Authorization": f"Bearer {self.credentials.token}",
                "Accept": "application/json"
            }
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching message {message_id}: {str(e)}")
            return None

    def _parse_date(self, date_str):
        """Parse date string to timezone-aware datetime"""
        try:
            if not date_str:
                print("Empty date string, using current time")
                return datetime.now(timezone.utc)
            
            try:
                dt = parsedate_to_datetime(date_str)
            except Exception as e:
                print(f"Failed to parse with parsedate_to_datetime: {e}")
                # Try alternative parsing with dateutil
                try:
                    dt = parser.parse(date_str)
                except Exception as e2:
                    print(f"Failed to parse with dateutil: {e2}")
                    return datetime.now(timezone.utc)
                
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        
        except Exception as e:
            print(f"Error in _parse_date: {str(e)}")
            return datetime.now(timezone.utc)

    def _is_recent_message(self, message_date, after_time):
        """Check if message is after the given time"""
        try:
            if not message_date or not after_time:
                return True
                
            # Convert after_time to UTC if it's not timezone-aware
            if after_time.tzinfo is None:
                after_time = after_time.replace(tzinfo=timezone.utc)
                
            # Parse message date
            parsed_date = self._parse_date(message_date)
            if not parsed_date:
                return True  # Include messages with unparseable dates
                
            # Compare dates
            return parsed_date >= after_time
            
        except Exception as e:
            print(f"Error comparing dates: {str(e)}")
            return True  # Include messages with date comparison errors

    def _strip_html_advanced(self, text):
        """Advanced HTML and CSS cleaning"""
        if not text:
            return ""
            
        # Remove inline CSS
        text = re.sub(r'style="[^"]*"', '', text)
        text = re.sub(r'class="[^"]*"', '', text)
        text = re.sub(r'data-[a-zA-Z0-9\-]*="[^"]*"', '', text)
        
        # Remove common HTML attributes
        text = re.sub(r'align="[^"]*"', '', text)
        text = re.sub(r'width="[^"]*"', '', text)
        text = re.sub(r'height="[^"]*"', '', text)
        text = re.sub(r'bgcolor="[^"]*"', '', text)
        text = re.sub(r'cellpadding="[^"]*"', '', text)
        text = re.sub(r'cellspacing="[^"]*"', '', text)
        
        # Remove all HTML tags except basic formatting
        allowed_tags = ['p', 'br', 'b', 'i', 'u', 'strong', 'em']
        for tag in allowed_tags:
            text = text.replace(f'<{tag}>', f' {tag}_start ')
            text = text.replace(f'</{tag}>', f' {tag}_end ')
        
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Restore basic formatting
        for tag in allowed_tags:
            text = text.replace(f'{tag}_start', f'<{tag}>')
            text = text.replace(f'{tag}_end', f'</{tag}>')
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _clean_text(self, text):
        """Clean and structure the text content"""
        if not text:
            return ""
        
        # First pass: basic HTML entity conversion
        text = html.unescape(text)
        
        # Advanced HTML cleaning
        text = self._strip_html_advanced(text)
        
        # Remove common email markers and formatting
        markers = [
            '<html>', '</html>', '<body>', '</body>', '<head>', '</head>',
            '<style>', '</style>', '<script>', '</script>', '<meta', '<!DOCTYPE',
            '<!--', '-->', '<div>', '</div>', '<tr>', '</tr>', '<td>', '</td>',
            '<table>', '</table>', '<br>', '<br/>', '<p>', '</p>', '<span>', '</span>',
            '<a>', '</a>', '<img>', '</img>', '<font>', '</font>', '<center>', '</center>',
            '<tbody>', '</tbody>', '<thead>', '</thead>', '<tfoot>', '</tfoot>'
        ]
        for marker in markers:
            text = text.replace(marker, '\n')
        
        # Clean up lines
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith(('<!', '<?', '//', '/*', '*/', '*', '-webkit')):
                # Remove CSS-like content
                if not any(css_term in line.lower() for css_term in [
                    'margin', 'padding', 'font-', 'text-', '-webkit-', 'background-',
                    'border-', 'color:', 'width:', 'height:', 'style=', 'class='
                ]):
                    lines.append(line)
        
        # Join lines and clean up spacing
        text = ' '.join(lines)
        
        # Remove multiple spaces and clean up
        text = ' '.join(text.split())
        
        # Final cleanup of any remaining special characters
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('\\n', '\n')
        text = text.replace('\\r', '')
        text = text.replace('\\t', ' ')
        
        return text.strip()

    def _extract_body(self, payload):
        """Extract email body from payload"""
        if not payload:
            return ""
        
        text_parts = []
        
        def extract_part(part):
            """Recursively extract text from message parts"""
            if 'body' in part:
                if 'data' in part['body']:
                    try:
                        decoded_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        return self._clean_text(decoded_text)
                    except Exception as e:
                        print(f"Error decoding body part: {str(e)}")
                        return ""
            
            if 'parts' in part:
                part_texts = []
                for subpart in part['parts']:
                    mime_type = subpart.get('mimeType', '')
                    if mime_type.startswith('text/'):
                        part_text = extract_part(subpart)
                        if part_text:
                            part_texts.append(part_text)
                return '\n'.join(filter(None, part_texts))
            
            return ""
        
        # Extract text from the main payload
        main_text = extract_part(payload)
        if main_text:
            text_parts.append(main_text)
        
        # Join all text parts and clean
        full_text = '\n'.join(filter(None, text_parts))
        return self._clean_text(full_text)

    def _parse_email_address(self, address_string):
        """Parse email address from string that might contain name and email"""
        try:
            # Handle empty or None
            if not address_string:
                return {'name': '', 'email': ''}
            
            # Try to extract email using regex
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address_string)
            email = email_match.group(0) if email_match else ''
            
            # Extract name
            name = address_string
            if '<' in address_string and '>' in address_string:
                name = address_string.split('<')[0].strip()
                if not email:
                    email = address_string.split('<')[1].split('>')[0].strip()
            elif '(' in address_string and ')' in address_string:
                name = address_string.split('(')[1].split(')')[0].strip()
            elif email:
                name = address_string.replace(email, '').strip()
            
            # Clean up name
            name = name.strip('" \'')
            
            # If no name found, use email
            if not name and email:
                name = email.split('@')[0]
            
            return {
                'name': name,
                'email': email
            }
        except Exception as e:
            print(f"Error parsing email address '{address_string}': {str(e)}")
            return {'name': address_string, 'email': ''}

    def _parse_recipients(self, recipients_string):
        """Parse multiple recipients from comma-separated string"""
        try:
            if not recipients_string:
                return []
            
            # Split by comma, but not by commas within quotes or brackets
            recipients = []
            current = ''
            in_quotes = False
            in_brackets = False
            
            for char in recipients_string:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == '<':
                    in_brackets = True
                elif char == '>':
                    in_brackets = False
                elif char == ',' and not in_quotes and not in_brackets:
                    if current.strip():
                        recipients.append(current.strip())
                    current = ''
                    continue
                current += char
            
            if current.strip():
                recipients.append(current.strip())
            
            # Parse each recipient
            return [self._parse_email_address(r) for r in recipients]
        except Exception as e:
            print(f"Error parsing recipients '{recipients_string}': {str(e)}")
            return [{'name': recipients_string, 'email': ''}]

    def get_message_details(self, message_id):
        """Get details of a specific message"""
        try:
            # Get the message with full format
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            recipients = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Get message body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
            elif 'body' in message['payload']:
                if 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'recipients': recipients,
                'body': body,
                'snippet': message.get('snippet', ''),
                'has_attachments': bool(message.get('payload', {}).get('parts', [])),
                'date': date,
                'star': 'STARRED' in message.get('labelIds', []),
                'label': ','.join(message.get('labelIds', []))
            }
        except Exception as e:
            print(f"Error getting message details: {str(e)}")
            return None

    def authenticate(self):
        """Handle Gmail OAuth2 authentication"""
        try:
            credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
            token_dir = os.path.join(os.path.dirname(__file__), 'token files')

            # Create token directory if it doesn't exist
            if not os.path.exists(token_dir):
                os.makedirs(token_dir)

            # Start new authentication flow
            print("Starting new authentication flow...")
            
            # Check if credentials file exists
            if not os.path.exists(credentials_path):
                print(f"Credentials file not found at: {credentials_path}")
                return False
                
            try:
                flow = Flow.from_client_secrets_file(credentials_path, self.scopes)
            except Exception as e:
                print(f"Error loading credentials file: {str(e)}")
                return False
            
            # Find available port with wider range and more attempts
            try:
                # Try common alternative ports if default port is in use
                for port in [5000, 5001, 8000, 8080, 8888, 3000, 9000]:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind(('127.0.0.1', port))
                            print(f"Using port {port} for OAuth flow")
                            break
                    except OSError:
                        continue
                else:
                    # If all common ports are taken, try to find any available port
                    port = self.find_available_port(10000, 1000)
                    print(f"Using fallback port {port} for OAuth flow")
            except Exception as e:
                print(f"Error finding available port: {str(e)}")
                print("Trying with default port anyway...")
                port = 8080  # Fallback to a default port
            
            try:
                # Configure timeout and success message
                success_message = 'Authentication successful! You can now close this window and return to the application.'
                
                # Run the flow with more explicit instructions
                print(f"Starting OAuth flow on port {port}... Please complete authentication in the browser window.")
                credentials = flow.run_local_server(
                    port=port,
                    success_message=success_message,
                    open_browser=True,
                    timeout_seconds=300  # 5 minutes timeout
                )
            except Exception as e:
                print(f"Error during OAuth flow: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
            
            if not credentials:
                print("Failed to get credentials from OAuth flow")
                return False
                
            # Get user email
            try:
                service = GmailAPI(credentials=credentials)
                profile = service.get_user_profile()
                user_email = profile.get('emailAddress')
                
                if not user_email:
                    print("Could not get user email from profile")
                    return False
                    
                # Save the new token
                token_filename = f"token_{user_email.replace('@', '_at_')}.json"
                token_path = os.path.join(token_dir, token_filename)
                
                # Remove any existing token files for this user
                existing_tokens = [f for f in os.listdir(token_dir) if f.startswith(f"token_{user_email.replace('@', '_at_')}")]
                for token_file in existing_tokens:
                    try:
                        os.remove(os.path.join(token_dir, token_file))
                    except Exception as e:
                        print(f"Error removing old token file: {str(e)}")
                
                # Save new token
                with open(token_path, 'w') as token:
                    token.write(credentials.to_json())
                
                # Store credentials and service
                self.credentials = credentials
                self.service = service
                self.current_user = user_email
                
                print(f"Successfully authenticated and saved token for {user_email}")
                return True
                
            except Exception as e:
                print(f"Error getting user profile: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            traceback.print_exc()
            return False

    def find_available_port(self, start_port=5000, max_attempts=100):
        """Find an available port to run the server on"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("Could not find an available port")

    def get_user_email(self):
        """Get the authenticated user's email address"""
        try:
            if not self.service:
                return None
            profile = self.service.get_user_profile()
            return profile.get('emailAddress')
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
            return None