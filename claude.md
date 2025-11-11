# Claude Code Plan: Voice-First AI Email Agent

## Project Overview

This is a production-ready, voice-first AI email agent built with:
- **LangGraph** for deterministic workflow orchestration
- **MCP-optimized CLI tools** for efficient execution
- **Supabase pgvector** for RAG knowledge base
- **Google Cloud APIs** for speech-to-text and text-to-speech
- **Direct Gmail API** access for email operations
- **FastAPI/WebSocket** for real-time voice interaction

## Architecture

```
User Voice Input
    ↓
[WebSocket Server]
    ↓
[STT: voice_cli.py] → Transcribed Text
    ↓
[LangGraph Orchestrator]
    ├→ Intent Classification (LLM)
    ├→ Route by Intent
    │   ├→ Draft Email (RAG + LLM)
    │   ├→ Retrieve Info (RAG Search)
    │   ├→ Manage Inbox (Gmail API)
    │   └→ Read Email (Gmail API)
    ↓
Response Text
    ↓
[TTS: voice_cli.py] → Audio Response
    ↓
[WebSocket Server] → User
```

## File Structure

```
voice-email-agent/
├── src/
│   ├── main.py              # FastAPI/WebSocket server
│   ├── workflow.py          # LangGraph orchestrator
│   └── config.py            # Configuration management
├── tools/
│   ├── email_cli.py         # Gmail operations (MCP-optimized)
│   ├── rag_cli.py           # RAG/knowledge base (MCP-optimized)
│   └── voice_cli.py         # STT/TTS (MCP-optimized)
├── tests/
│   └── test_workflow.py     # TDD test suite
├── scripts/
│   ├── setup_supabase.sql   # Database schema
│   └── ingest_data.py       # Data ingestion
├── requirements.txt
├── Dockerfile
├── DEPLOYMENT.md
└── README.md
```

## Core Components

### 1. MCP-Optimized CLI Tools

All tools follow the **Code Execution with MCP** pattern:
- Accept input via command-line arguments
- Execute operations outside the LLM context
- Return results as JSON to stdout
- Handle errors gracefully

**Benefits:**
- Reduced token usage (large data processed outside LLM)
- Improved reliability (no hallucination in tool execution)
- Easy testing and debugging

### 2. LangGraph Workflow

The workflow uses a **deterministic state machine** instead of relying on LLM instruction-following:

1. **classify_intent**: Uses LLM to classify user intent into one of 5 categories
2. **route_by_intent**: Deterministic routing based on classified intent
3. **Handler nodes**: Execute specific logic for each intent
4. **END**: Return final response

**Key Design Decision:** LLM is ONLY used for:
- Intent classification (constrained output)
- Content generation (drafting emails, answering questions)

All workflow logic is deterministic Python code.

### 3. RAG Knowledge Base

Uses **Supabase pgvector** for semantic search:
- Documents stored with embeddings (OpenAI text-embedding-3-small)
- Vector similarity search via PostgreSQL function
- Metadata filtering for categorization

### 4. Speech-to-Speech Pipeline

**Streaming architecture:**
1. Client sends audio via WebSocket
2. Server transcribes (Google Cloud STT)
3. Server processes through LangGraph
4. Server synthesizes speech (Google Cloud TTS)
5. Server streams audio back to client

## Development Workflow

### Phase 1: Setup ✅
- Project structure created
- Dependencies defined
- Configuration management implemented

### Phase 2: CLI Tools ✅
- `email_cli.py`: Gmail API integration
- `rag_cli.py`: Supabase pgvector integration
- `voice_cli.py`: Google Cloud STT/TTS integration

### Phase 3: LangGraph Orchestrator ✅
- State machine workflow
- Intent classification
- Handler nodes for each intent

### Phase 4: FastAPI Server ✅
- WebSocket endpoint for voice
- REST endpoint for text
- Streaming speech-to-speech pipeline

### Phase 5: Database & Data ✅
- Supabase schema setup
- Data ingestion scripts
- Sample business data

### Phase 6: Testing & Deployment ✅
- TDD test suite
- Dockerfile for containerization
- Deployment guide for Google Cloud Run

## Testing Strategy

### TDD Test Cases

1. **TDD-1: Draft Email**
   - Input: "Draft a proposal email for Acme Corp"
   - Expected: Email draft with subject and body

2. **TDD-2: Retrieve Info**
   - Input: "What is our refund policy?"
   - Expected: Answer from RAG knowledge base

3. **TDD-3: Manage Inbox**
   - Input: "Label the last email as Important"
   - Expected: Confirmation of label applied

4. **TDD-4: Read Email**
   - Input: "Read me my unread emails"
   - Expected: Summary of unread emails

5. **TDD-5: Voice Readout**
   - Input: Audio file with question
   - Expected: Audio response

6. **TDD-6: Error Handling**
   - Input: Invalid/empty input
   - Expected: Graceful error handling

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_workflow.py::TestIntentClassification -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in your API keys

# Run the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t voice-email-agent .

# Run
docker run -p 8000:8000 --env-file .env voice-email-agent
```

### Google Cloud Run

See `DEPLOYMENT.md` for detailed instructions.

## Configuration

All configuration is managed via environment variables (see `.env.example`):

**Required:**
- `OPENAI_API_KEY`: For LLM and embeddings
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `GMAIL_CLIENT_ID`: Gmail OAuth client ID
- `GMAIL_CLIENT_SECRET`: Gmail OAuth client secret
- `GMAIL_REFRESH_TOKEN`: Gmail OAuth refresh token
- `GOOGLE_CLOUD_PROJECT`: Google Cloud project ID

**Optional:**
- `SENTRY_DSN`: For error tracking
- `ENVIRONMENT`: development/production
- `LOG_LEVEL`: INFO/DEBUG/WARNING/ERROR

## Context Engineering

### Progressive Disclosure

The MCP-optimized architecture ensures the LLM only sees what it needs:

1. **Intent Classification**: Only sees user input + intent options
2. **Draft Email**: Only sees user input + relevant RAG results
3. **Retrieve Info**: Only sees user input + RAG results
4. **Manage Inbox**: Only sees user input + action extraction prompt

### Token Efficiency

- Large email bodies processed by CLI tools, not LLM
- RAG results limited to top 3-5 matches
- Embeddings generated outside LLM context

## Best Practices

### When Modifying the Code

1. **Update tests first** (TDD approach)
2. **Keep CLI tools pure** (no LLM calls in tools)
3. **Maintain deterministic routing** (no LLM-based workflow decisions)
4. **Log all errors** (use Sentry for production)

### When Adding New Features

1. Create a new CLI tool if needed
2. Add a new intent to the workflow
3. Implement the handler node
4. Add routing logic
5. Write tests
6. Update documentation

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `PYTHONPATH` includes project root
2. **API key errors**: Verify all keys in `.env` are correct
3. **Supabase connection**: Check firewall and VPC settings
4. **Gmail OAuth**: Refresh token may expire, regenerate if needed

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn src.main:app --reload --log-level debug
```

## Next Steps

1. **Build Web Client**: Create a React/Vue app for the WebSocket interface
2. **User Authentication**: Add JWT-based auth for multi-user support
3. **Advanced RAG**: Implement hybrid search (vector + keyword)
4. **Email Attachments**: Add support for sending/receiving attachments
5. **Calendar Integration**: Extend to Google Calendar operations

## Support

For questions or issues:
1. Check the README.md
2. Review the DEPLOYMENT.md guide
3. Run the test suite to validate setup
4. Check logs for error details

---

**Built with:** Python 3.11, FastAPI, LangGraph, Supabase, Google Cloud APIs
**Deployment:** Google Cloud Run (serverless)
**License:** MIT
