import os
import pandas as pd
from io import BytesIO
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
import openpyxl

from openai import AsyncOpenAI
from supabase import create_client, Client

from .crawl_pydantic_ai_docs import (
    ProcessedChunk,
    chunk_text,
    insert_chunk
)

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def build_service():
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
            
    return build('drive', 'v3', credentials=creds)

async def process_csv_data(file_obj, name: str) -> list[ProcessedChunk]:
    chunks = []
    df = pd.read_csv(file_obj)
    
    # Process each row as a chunk
    for _, row in df.iterrows():
        content = "\n".join([f"{col}: {val}" for col, val in row.items()])
        chunk = ProcessedChunk(
            url=f"gdrive://{name}",
            title=name,
            summary=f"Row from {name}",
            content=content,
            embedding=None
        )
        chunks.append(chunk)
        
    return chunks

async def process_excel_data(file_obj, name: str) -> list[ProcessedChunk]:
    chunks = []
    df = pd.read_excel(file_obj)
    
    # Process each row as a chunk
    for _, row in df.iterrows():
        content = "\n".join([f"{col}: {val}" for col, val in row.items()])
        chunk = ProcessedChunk(
            url=f"gdrive://{name}",
            title=name,
            summary=f"Row from {name}",
            content=content,
            embedding=None
        )
        chunks.append(chunk)
        
    return chunks

async def process_file(service, file: Dict[str, str]):
    file_id = file['id']
    mime_type = file['mimeType']
    name = file['name']
    
    try:
        request = service.files().get_media(fileId=file_id)
        file_obj = BytesIO()
        downloader = MediaIoBaseDownload(file_obj, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_obj.seek(0)
        
        # Process based on file type
        if mime_type == 'text/csv':
            chunks = await process_csv_data(file_obj, name)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            chunks = await process_excel_data(file_obj, name)
        else:
            print(f"Unsupported file type: {mime_type}")
            return
        
        # Insert chunks into database
        for chunk in chunks:
            await insert_chunk(chunk)
            
    except Exception as e:
        print(f"Error processing file {name}: {e}")

async def process_folder(folder_id: str):
    service = build_service()
    
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        
        for file in files:
            await process_file(service, file)
            
    except Exception as e:
        print(f"Error processing folder: {e}")

if __name__ == "__main__":
    import asyncio
    folder_id = os.getenv('GDRIVE_FOLDER_ID')
    if not folder_id:
        print("Please set GDRIVE_FOLDER_ID environment variable")
        sys.exit(1)
    asyncio.run(process_folder(folder_id))