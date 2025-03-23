# Pydantic RAG Agents

A RAG (Retrieval-Augmented Generation) system using Pydantic AI agents with MCP-based communication for automated document processing and querying.

## Architecture

The system uses a Message Control Point (MCP) architecture for inter-agent communication:

```
                     ┌─────────────────┐
                     │  DriveWatcher   │
                     │      MCP        │
                     └────────┬────────┘
                              │
                              │ new_file
                              ▼
                     ┌─────────────────┐
                     │    Document     │
                     │   Processor     │
                     └────────┬────────┘
                              │
                              │ file_processed
                              ▼
┌──────────────┐     ┌─────────────────┐
│   Supabase   │◄────┤   RAG Expert    │
│Vector Search │     │      MCP        │
└──────────────┘     └─────────────────┘
```

### Components

1. **Message Control Point (MCP)**
   - Handles asynchronous message routing between agents
   - Supports publish/subscribe pattern
   - Provides message queueing and error handling

2. **DriveWatcher Agent**
   - Monitors Google Drive for file changes
   - Publishes file events to MCP
   - Maintains processing state

3. **Document Processor**
   - Processes various file types (CSV, Excel, etc.)
   - Generates embeddings for content
   - Stores processed data in Supabase

4. **RAG Expert**
   - Handles user queries
   - Uses vector search for relevant context
   - Generates responses using OpenAI

## Message Types

1. **DriveWatcher → Document Processor**
   - `new_file`: New file detected
   - `update_file`: File modified
   - `delete_file`: File removed

2. **Document Processor → RAG Expert**
   - `file_processed`: File successfully processed
   - `file_error`: Error during processing

3. **RAG Expert → UI**
   - `query_response`: Response to user query
   - `processing_error`: Error during query

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
OPENAI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_SERVICE_KEY=your_key
GDRIVE_FOLDER_ID=your_folder_id
```

3. Run the system:
```bash
# Start the UI
streamlit run streamlit_ui.py

# Start the watcher (in another terminal)
python -c "from agents.gdrive_watcher import DriveWatcher; import asyncio; asyncio.run(DriveWatcher().start())"
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request