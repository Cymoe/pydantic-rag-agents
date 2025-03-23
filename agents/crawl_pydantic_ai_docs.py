"""
Web crawler for Pydantic AI documentation.
"""

import os
import sys
import logging
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import aiohttp
from openai import AsyncOpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

@dataclass
class ProcessedChunk:
    """A processed chunk of documentation."""
    url: str
    title: str
    summary: str
    content: str
    embedding: Optional[List[float]] = None

# Initialize OpenAI and Supabase clients
load_dotenv()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

async def get_embedding(text: str) -> List[float]:
    """Get an embedding for a piece of text."""
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

async def chunk_text(text: str, url: str, title: str) -> List[ProcessedChunk]:
    """Split text into chunks with some overlap."""
    words = text.split()
    chunk_size = 1000
    overlap = 100
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        chunks.append(ProcessedChunk(
            url=url,
            title=title,
            summary=f"Part {len(chunks) + 1} of {title}",
            content=chunk_text
        ))
    
    return chunks

async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into the database."""
    if not chunk.embedding:
        chunk.embedding = await get_embedding(chunk.content)
    
    data = {
        "url": chunk.url,
        "title": chunk.title,
        "summary": chunk.summary,
        "content": chunk.content,
        "embedding": chunk.embedding,
        "source": "pydantic_ai_docs"
    }
    
    result = supabase.table("site_pages").insert(data).execute()
    return result

async def process_chunk(chunk: ProcessedChunk, url: str):
    """Process and store a single chunk."""
    try:
        await insert_chunk(chunk)
        logging.info(f"Processed chunk from {url}")
    except Exception as e:
        logging.error(f"Error processing chunk from {url}: {e}")

async def crawl_page(url: str, session: aiohttp.ClientSession) -> List[ProcessedChunk]:
    """Crawl a single documentation page."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Error fetching {url}: {response.status}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract main content
            main_content = soup.find('main')
            if not main_content:
                logging.warning(f"No main content found at {url}")
                return []
            
            # Get title
            title = soup.find('h1')
            title_text = title.get_text() if title else url
            
            # Process content
            content = main_content.get_text()
            chunks = await chunk_text(content, url, title_text)
            
            return chunks
            
    except Exception as e:
        logging.error(f"Error crawling {url}: {e}")
        return []

async def main():
    """Main crawling function."""
    base_url = "https://pydantic-ai.readthedocs.io/en/latest/"
    
    async with aiohttp.ClientSession() as session:
        # Start with the main page
        chunks = await crawl_page(base_url, session)
        
        # Process chunks
        tasks = []
        for chunk in chunks:
            task = asyncio.create_task(process_chunk(chunk, base_url))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('crawler.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Log configuration
    logging.info("Starting crawler with configuration:")
    logging.info(f"Supabase URL: {os.getenv('SUPABASE_URL')}")
    logging.info(f"OpenAI API Key set: {bool(os.getenv('OPENAI_API_KEY'))}")

    asyncio.run(main())

# Export the main function and key utilities
__all__ = [
    'crawl_pydantic_ai_docs',
    'ProcessedChunk',
    'chunk_text',
    'insert_chunk',
    'process_chunk',
    'get_embedding',
]

# Rename main to crawl_pydantic_ai_docs for better clarity
crawl_pydantic_ai_docs = main