# Voice-First AI Email Agent

A robust, production-ready AI email agent with voice-first interaction, built on LangGraph orchestration, MCP-optimized tools, and Supabase for persistent memory.

## Architecture

The system uses a hybrid architecture combining:

- **LangGraph** for deterministic, stateful orchestration
- **MCP-optimized CLI tools** for efficient execution
- **Supabase** (with pgvector) for vector search and structured data
- **Google Cloud APIs** for streaming speech-to-text and text-to-speech
- **Direct Gmail API** access for email operations

## Features

- **Voice-First Interaction:** Natural speech-to-speech conversation
- **Email Management:** Draft, send, label, archive, and search emails
- **RAG Knowledge Base:** Access business FAQs, templates, and policies
- **Writing Style Learning:** Adapts to your communication style
- **Real-Time Notifications:** Get pinged for important emails
- **Cloud-Native:** Designed for scalable deployment on Google Cloud Run

## Project Structure

```
voice-email-agent/
├── src/
│   ├── main.py              # FastAPI/Websocket server
│   ├── workflow.py          # LangGraph orchestrator
│   └── config.py            # Configuration management
├── tools/
│   ├── email_cli.py         # Gmail operations
│   ├── rag_cli.py           # RAG/knowledge base operations
│   └── voice_cli.py         # STT/TTS operations
├── tests/
│   └── test_workflow.py     # TDD test suite
├── scripts/
│   └── ingest_data.py       # RAG data ingestion
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

1. Python 3.11+
2. Supabase account
3. Google Cloud project with Speech-to-Text, Text-to-Speech, and Gmail APIs enabled
4. OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd voice-email-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

5. Set up Supabase schema (see `scripts/setup_supabase.sql`)

### Running the Application

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Development

This project follows a Test-Driven Development (TDD) approach. Run tests with:

```bash
pytest tests/ -v
```

## Deployment

The application is containerized and ready for deployment to Google Cloud Run. See `Dockerfile` for details.

## License

MIT
