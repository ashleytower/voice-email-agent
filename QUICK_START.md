# Quick Start Guide

Get your voice-first AI email agent up and running in **30 minutes**.

## What You'll Need

- [ ] Supabase account (free tier works)
- [ ] OpenAI API key
- [ ] Gmail account for testing
- [ ] Google Cloud account (for STT/TTS)

## Step-by-Step Setup

### 1. Clone the Repository (2 minutes)

```bash
git clone https://github.com/ashleytower/voice-email-agent.git
cd voice-email-agent
```

### 2. Install Dependencies (3 minutes)

```bash
pip install -r requirements.txt
```

### 3. Set Up Supabase (10 minutes)

#### 3.1 Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Fill in:
   - Name: `voice-email-agent`
   - Password: (generate and save)
   - Region: (closest to you)
4. Click "Create new project"
5. Wait 2-3 minutes for initialization

#### 3.2 Run the Schema

1. In Supabase, click **SQL Editor** (left sidebar)
2. Click "New Query"
3. Open `scripts/setup_supabase_complete.sql` from this repo
4. **Copy all the SQL** and paste into the editor
5. Click **"Run"**
6. You should see: "Success. No rows returned"

#### 3.3 Get Your Credentials

1. Click **Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon public key:** (long string)
   - **service_role key:** (click "Reveal" to see it)

### 4. Configure Environment Variables (5 minutes)

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OpenAI
OPENAI_API_KEY=sk-...

# Gmail (we'll set this up later)
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=

# Google Cloud (we'll set this up later)
GOOGLE_CLOUD_PROJECT=
```

### 5. Ingest Sample Data (2 minutes)

```bash
python scripts/ingest_business_data.py --sample
```

You should see:
```
✅ Documents: 5
✅ Contacts: 3
✅ Proposals: 2
✅ FAQs: 3
```

### 6. Test the RAG System (2 minutes)

```bash
python tests/test_rag_demo.py
```

You should see:
```
✅ RAG System Test: PASS
✅ Contact Retrieval: PASS
✅ Proposal Templates: PASS
🎉 All tests passed!
```

### 7. Run the Server (1 minute)

```bash
uvicorn src.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 8. Test the API (2 minutes)

Open a new terminal and test:

```bash
curl -X POST http://localhost:8000/api/text \
  -H "Content-Type: application/json" \
  -d '{"text": "What is our refund policy?"}'
```

You should get a JSON response with the answer!

## What's Working Now

✅ **RAG System** - The agent can search your business knowledge  
✅ **Text API** - You can ask questions via HTTP  
✅ **LangGraph Orchestrator** - The workflow is ready  
✅ **Supabase Storage** - All your data is in the cloud  

## What's Not Working Yet

❌ **Voice Input/Output** - Need Google Cloud STT/TTS setup  
❌ **Gmail Integration** - Need OAuth credentials  
❌ **WebSocket** - Need a web client  

## Next Steps

### To Add Voice (15 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Speech-to-Text API** and **Text-to-Speech API**
4. Create a service account and download the JSON key
5. Set `GOOGLE_CLOUD_PROJECT` in `.env`
6. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your JSON key

### To Add Gmail (20 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Gmail API**
3. Create OAuth 2.0 credentials
4. Follow the [Gmail API Quickstart](https://developers.google.com/gmail/api/quickstart/python)
5. Add credentials to `.env`

### To Deploy (30 minutes)

See `DEPLOYMENT.md` for full instructions on deploying to Google Cloud Run.

## Troubleshooting

### "Connection error" when running scripts

**Problem:** Can't connect to Supabase

**Solution:** Check that `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct in `.env`

### "No results found" when testing RAG

**Problem:** No data in Supabase

**Solution:** Run `python scripts/ingest_business_data.py --sample` again

### "Module not found" errors

**Problem:** Dependencies not installed

**Solution:** Run `pip install -r requirements.txt`

### Server won't start

**Problem:** Port 8000 already in use

**Solution:** Use a different port: `uvicorn src.main:app --reload --port 8001`

## Getting Help

- **Documentation:** See `SUPABASE_SETUP.md` for detailed Supabase guide
- **Deployment:** See `DEPLOYMENT.md` for cloud deployment
- **Architecture:** See `PROJECT_SUMMARY.md` for system overview
- **GitHub Issues:** https://github.com/ashleytower/voice-email-agent/issues

## What to Add to Supabase

Now that the system is working, you should add **your real business data**:

### 1. FAQs

Add your most common customer questions:

```bash
# Create a JSON file: my_faqs.json
{
  "faqs": [
    {
      "category": "Billing",
      "question": "How do I cancel my subscription?",
      "answer": "You can cancel anytime in your account settings...",
      "keywords": ["cancel", "subscription", "billing"]
    }
  ]
}

# Ingest it
python scripts/ingest_business_data.py --json my_faqs.json
```

### 2. Contacts

Add your key contacts:

```bash
{
  "contacts": [
    {
      "name": "Jane Doe",
      "email": "jane@client.com",
      "company": "Client Corp",
      "role": "CEO",
      "relationship_type": "client",
      "notes": "Prefers email over phone"
    }
  ]
}
```

### 3. Proposal Templates

Add your proposal templates:

```bash
{
  "proposals": [
    {
      "title": "Standard Consulting Proposal",
      "template_name": "consulting_v1",
      "content": "# Proposal for [CLIENT]\n\n..."
    }
  ]
}
```

### 4. Business Knowledge

Add any documents that the agent should know:

```bash
{
  "documents": [
    {
      "title": "Company Overview",
      "content": "We are a company that...",
      "doc_type": "general",
      "category": "company"
    }
  ]
}
```

## You're Ready!

Your AI email agent is now running locally with:

- ✅ A working RAG system that knows your business
- ✅ A REST API for text-based interaction
- ✅ A scalable Supabase backend
- ✅ A deterministic LangGraph workflow

Next: Add your real business data and deploy to the cloud!
