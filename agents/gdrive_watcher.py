"""
Google Drive watcher agent that monitors for file changes and delegates processing.
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .message_control_point import MessageControlPoint

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')

class DriveWatcher:
    def __init__(self):
        self.processed_files: Dict[str, str] = {}  # file_id -> last_modified
        self.mcp = MessageControlPoint(
            name="drive_watcher",
            handlers={
                "file_processed": self.handle_file_processed,
                "file_error": self.handle_file_error
            },
            queue=asyncio.Queue()
        )
        self.load_processed_files()
        
    def load_processed_files(self):
        """Load the list of processed files from disk."""
        try:
            with open('processed_files.json', 'r') as f:
                self.processed_files = json.load(f)
        except FileNotFoundError:
            self.processed_files = {}
            
    def save_processed_files(self):
        """Save the list of processed files to disk."""
        with open('processed_files.json', 'w') as f:
            json.dump(self.processed_files, f)
            
    def get_credentials(self):
        """Get valid user credentials from storage or user input."""
        creds = None
        token_path = 'credentials/token.json'
        
        # Check if we have valid credentials
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            os.makedirs('credentials', exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        return creds

    async def handle_file_processed(self, data: Dict[str, Any]):
        """Handle successful file processing"""
        file_id = data["file_id"]
        self.processed_files[file_id] = datetime.now(timezone.utc).isoformat()
        self.save_processed_files()

    async def handle_file_error(self, data: Dict[str, Any]):
        """Handle file processing errors"""
        print(f"Error processing file {data['file_id']}: {data['error']}")

    async def check_for_changes(self):
        """Check for new or modified files in the Drive folder."""
        try:
            service = build('drive', 'v3', credentials=self.get_credentials())
            
            results = service.files().list(
                q=f"'{FOLDER_ID}' in parents",
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            current_files = results.get('files', [])
            
            for file in current_files:
                file_id = file['id']
                modified_time = file['modifiedTime']
                
                if (file_id not in self.processed_files or 
                    self.processed_files[file_id] != modified_time):
                    print(f"\nProcessing file: {file['name']}")
                    # Publish to MCP instead of direct call
                    await self.mcp.publish("new_file", {
                        "service": service,
                        "file": file
                    })
            
            # Check for deleted files
            stored_ids = set(self.processed_files.keys())
            current_ids = {f['id'] for f in current_files}
            deleted_ids = stored_ids - current_ids
            
            for file_id in deleted_ids:
                print(f"File {file_id} was deleted")
                del self.processed_files[file_id]
                self.save_processed_files()
                
        except Exception as e:
            print(f"Error checking for changes: {e}")
            
    async def start(self):
        """Start the watcher service."""
        print("Starting Drive Watcher...")
        await self.mcp.start()  # Start processing messages
        while True:
            await self.check_for_changes()
            await asyncio.sleep(60)  # Check every minute