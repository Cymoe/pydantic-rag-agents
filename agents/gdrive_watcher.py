import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .crawl_gdrive_docs import process_file

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')

class DriveWatcher:
    def __init__(self):
        self.processed_files: Dict[str, str] = {}
        self.load_processed_files()
        
    def load_processed_files(self):
        try:
            with open('processed_files.json', 'r') as f:
                self.processed_files = json.load(f)
        except FileNotFoundError:
            self.processed_files = {}
            
    def save_processed_files(self):
        with open('processed_files.json', 'w') as f:
            json.dump(self.processed_files, f)
            
    def get_credentials(self):
        creds = None
        token_path = 'credentials/token.json'
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
            os.makedirs('credentials', exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        return creds
    
    async def check_for_changes(self):
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
                    await process_file(service, file)
                    self.processed_files[file_id] = modified_time
                    self.save_processed_files()
            
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
        print("Starting Drive Watcher...")
        while True:
            await self.check_for_changes()
            await asyncio.sleep(60)  # Check every minute