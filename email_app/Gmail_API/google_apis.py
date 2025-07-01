import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import socket
import ssl

def create_service(credentials=None, client_secret_file=None, api_name='gmail', api_version='v1', scopes=None):
    """Create a Google API service instance with improved error handling"""
    try:
        # If credentials are provided directly, use them
        if credentials:
            try:
                service = build(api_name, api_version, credentials=credentials)
                print(f"{api_name} {api_version} service created successfully")
                return service
            except Exception as e:
                print(f"Error building service with provided credentials: {str(e)}")
                raise Exception(f"Failed to create service: {str(e)}")

        # Otherwise, try to create new credentials
        if not client_secret_file:
            raise ValueError("Either credentials or client_secret_file must be provided")

        creds = None
        token_dir = 'token files'
        token_file = f'token_{api_name}_{api_version}.json'
        token_path = os.path.join(token_dir, token_file)

        # Ensure token directory exists
        if not os.path.exists(token_dir):
            os.makedirs(token_dir)

        # Load existing credentials
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, scopes)
            except Exception as e:
                print(f"Error loading credentials: {str(e)}")
                if os.path.exists(token_path):
                    os.remove(token_path)
                creds = None

        # If credentials don't exist or are invalid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    print("Token refresh failed, initiating new authentication flow")
                    creds = None
                except Exception as e:
                    print(f"Error refreshing token: {str(e)}")
                    creds = None

            if not creds:
                try:
                    # Set up SSL context
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

                    # Configure socket timeout
                    socket.setdefaulttimeout(30)

                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secret_file, 
                        scopes,
                        redirect_uri='http://localhost:0'
                    )
                    creds = flow.run_local_server(port=0)

                    # Save credentials
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    print(f"Error in authentication flow: {str(e)}")
                    return None

        try:
            service = build(api_name, api_version, credentials=creds)
            print(f"{api_name} {api_version} service created successfully")
            return service
        except Exception as e:
            print(f"Error building service: {str(e)}")
            raise Exception(f"Failed to create service: {str(e)}")

    except Exception as e:
        print(f"Error in create_service: {str(e)}")
        raise Exception(f"Service creation failed: {str(e)}")