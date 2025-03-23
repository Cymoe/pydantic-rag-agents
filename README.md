# Pydantic RAG Agents

A collection of agents for building a Retrieval-Augmented Generation (RAG) system that processes and queries Pydantic AI documentation and business data.

## Features

- **Document Crawling**: Automated crawling of Pydantic AI documentation and Google Drive documents
- **Message Control Point (MCP) Architecture**: Efficient inter-agent communication
- **Vector Search**: Semantic search using OpenAI embeddings and Supabase vector store
- **RAG Expert**: AI-powered query processing and response generation

## Components

1. **DriveWatcher Agent** (`agents/gdrive_watcher.py`):
   - Monitors Google Drive folders for changes
   - Processes new and modified files
   - Integrates with MCP for notifications

2. **Document Processing Agent** (`agents/crawl_gdrive_docs.py`):
   - Processes various file types (CSV, Excel, etc.)
   - Generates chunks and embeddings
   - Stores processed data in Supabase

3. **Pydantic AI Crawler** (`agents/crawl_pydantic_ai_docs.py`):
   - Crawls Pydantic AI documentation
   - Processes content into searchable chunks
   - Maintains up-to-date documentation index

4. **RAG Expert Agent** (`agents/pydantic_ai_expert.py`):
   - Handles natural language queries
   - Performs semantic search
   - Generates contextual responses

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Cymoe/pydantic-rag-agents.git
   cd pydantic-rag-agents
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `GDRIVE_FOLDER_ID`
   - `LLM_MODEL` (defaults to "gpt-4")

## Usage

1. Start the DriveWatcher agent:
   ```python
   from agents.gdrive_watcher import DriveWatcher
   
   watcher = DriveWatcher()
   await watcher.start()
   ```

2. Process documents:
   ```python
   from agents.crawl_gdrive_docs import process_file
   from agents.crawl_pydantic_ai_docs import crawl_pydantic_ai_docs
   
   # Process Google Drive files
   await process_file(service, file_metadata)
   
   # Crawl Pydantic AI docs
   await crawl_pydantic_ai_docs()
   ```

3. Query the RAG system:
   ```python
   from agents.pydantic_ai_expert import pydantic_ai_expert
   
   # Query documentation
   response = await pydantic_ai_expert("How do I use Pydantic's Field class?", context_type="docs")
   print(response)
   
   # Query business data
   response = await pydantic_ai_expert("What were our Q4 sales?", context_type="business")
   print(response)
   ```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Pydantic](https://docs.pydantic.dev/) for their excellent data validation library
- [OpenAI](https://openai.com/) for their powerful language models and embeddings
- [Supabase](https://supabase.com/) for their vector store capabilities