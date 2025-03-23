"""
RAG expert agent for handling queries about Pydantic AI and business data.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any
from openai import AsyncOpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

@dataclass
class PydanticAIDeps:
    """Dependencies for the Pydantic AI expert."""
    supabase: Client
    openai_client: AsyncOpenAI

load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

deps = PydanticAIDeps(
    supabase=supabase,
    openai_client=openai_client
)

async def preprocess_query(query: str) -> str:
    """Extract key technical concepts from the query."""
    system_prompt = """
    You are a technical concept extractor. Given a query, identify and extract the key
    technical concepts that would be most relevant for searching documentation.
    Return these concepts in a comma-separated list.
    """
    
    response = await openai_client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.3
    )
    
    concepts = response.choices[0].message.content
    return f"{query} {concepts}"

async def search_documents(query: str, source: str = None) -> List[Dict[str, Any]]:
    """Search for relevant documents using vector similarity."""
    # Get query embedding
    query_embedding = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    
    # Search in Supabase
    query_params = {"query_embedding": query_embedding.data[0].embedding, "match_count": 5}
    if source:
        query_params["source"] = source
    
    result = supabase.rpc(
        "match_site_pages",
        query_params
    ).execute()
    
    return result.data

async def generate_response(query: str, context: List[Dict[str, Any]]) -> str:
    """Generate a response using the query and retrieved context."""
    # Prepare context string
    context_str = "\n\n".join([
        f"Source: {doc['url']}\n{doc['content']}"
        for doc in context
    ])
    
    system_prompt = """
    You are a helpful AI assistant with expertise in Pydantic AI and business data analysis.
    Use the provided context to answer questions accurately and concisely.
    If you're not sure about something, say so rather than making assumptions.
    """
    
    response = await openai_client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

async def run(query: str, context_type: str = "docs") -> str:
    """Run the RAG pipeline on a query."""
    try:
        # Preprocess query
        enhanced_query = await preprocess_query(query)
        
        # Search for relevant documents
        source = "pydantic_ai_docs" if context_type == "docs" else None
        context = await search_documents(enhanced_query, source)
        
        # Generate response
        response = await generate_response(query, context)
        
        return response
        
    except Exception as e:
        return f"Error processing query: {str(e)}"

# Export the agent
pydantic_ai_expert = run