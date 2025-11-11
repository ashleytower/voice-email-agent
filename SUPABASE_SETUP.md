# Supabase Setup Guide

This guide will walk you through setting up Supabase to store ALL your business data for the AI email agent.

## What Gets Stored in Supabase?

Your Supabase database will contain:

1. **📚 Knowledge Base (RAG)** - FAQs, policies, templates, general business info
2. **👥 Contacts** - All your business contacts with relationship context
3. **📄 Proposals** - Proposal templates and sent proposals
4. **📧 Email Context** - Cached email threads for fast retrieval (optional)
5. **⚙️ User Preferences** - Your writing style and settings
6. **❓ FAQs** - Organized, searchable frequently asked questions

## Step-by-Step Setup

### Step 1: Create a Supabase Project (5 minutes)

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in:
   - **Project Name:** `voice-email-agent` (or your preferred name)
   - **Database Password:** Generate a strong password (save this!)
   - **Region:** Choose closest to you (e.g., `us-east-1`)
4. Click "Create new project"
5. Wait 2-3 minutes for the project to initialize

### Step 2: Run the Database Schema (10 minutes)

1. In your Supabase project, click on the **SQL Editor** in the left sidebar
2. Click "New Query"
3. Open the file `scripts/setup_supabase_complete.sql` from this repository
4. **Copy the entire contents** of that file
5. **Paste** into the Supabase SQL Editor
6. Click **"Run"** (or press Ctrl/Cmd + Enter)
7. You should see: "Success. No rows returned"

**What this creates:**
- 7 tables: `documents`, `contacts`, `proposals`, `email_threads`, `email_messages`, `user_preferences`, `faqs`, `faq_categories`
- Vector search function: `match_documents()`
- Indexes for fast queries
- Triggers for auto-updating timestamps

### Step 3: Get Your Supabase Credentials (2 minutes)

1. In Supabase, click on the **Settings** icon (gear) in the left sidebar
2. Click **API** under "Project Settings"
3. You'll see two important values:

   **Copy these:**
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon public key:** `eyJhbG...` (long string)
   - **service_role key:** `eyJhbG...` (different long string - click "Reveal" to see it)

4. Add these to your `.env` file:
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=your_anon_key_here
   SUPABASE_SERVICE_KEY=your_service_role_key_here
   ```

⚠️ **Important:** The `service_role` key has full database access. Keep it secret!

### Step 4: Ingest Your Business Data (15-30 minutes)

Now you'll populate Supabase with your business knowledge.

#### Option A: Start with Sample Data (Recommended for testing)

```bash
cd voice-email-agent
python scripts/ingest_business_data.py --sample
```

This will add:
- 5 sample documents (refund policy, email templates, etc.)
- 3 sample contacts
- 2 proposal templates
- 3 FAQs

#### Option B: Add Your Real Business Data

**Method 1: JSON File (Recommended)**

1. Create a JSON file with your data (see format below)
2. Run:
   ```bash
   python scripts/ingest_business_data.py --json /path/to/your/data.json
   ```

**JSON Format:**
```json
{
  "documents": [
    {
      "title": "Refund Policy",
      "content": "Our refund policy is...",
      "doc_type": "policy",
      "category": "customer_service"
    }
  ],
  "contacts": [
    {
      "name": "John Smith",
      "email": "john@example.com",
      "company": "Acme Corp",
      "role": "CEO",
      "relationship_type": "client"
    }
  ],
  "proposals": [
    {
      "title": "Standard Consulting Proposal",
      "template_name": "consulting_v1",
      "content": "# Proposal\n\nWe propose..."
    }
  ],
  "faqs": [
    {
      "category": "Billing",
      "question": "How do I get a refund?",
      "answer": "You can request a refund by...",
      "keywords": ["refund", "billing", "payment"]
    }
  ]
}
```

**Method 2: Manual Entry via Supabase UI**

1. Go to your Supabase project
2. Click **Table Editor** in the left sidebar
3. Select a table (e.g., `documents`)
4. Click **"Insert row"**
5. Fill in the fields manually

### Step 5: Verify Your Data (2 minutes)

Check that your data was ingested correctly:

1. In Supabase, go to **Table Editor**
2. Click on the `documents` table
3. You should see your documents listed
4. Check other tables: `contacts`, `proposals`, `faqs`

You can also test the vector search:

1. Go to **SQL Editor**
2. Run this query:
   ```sql
   SELECT * FROM match_documents(
     (SELECT embedding FROM documents LIMIT 1),
     0.5,
     5
   );
   ```

### Step 6: Test the RAG System (5 minutes)

Now test that the agent can retrieve your data:

```bash
# Test the RAG CLI tool directly
python tools/rag_cli.py search --query "What is our refund policy?" --limit 3
```

You should see JSON output with your documents!

## What to Put in Each Table

### 📚 Documents Table (Knowledge Base)

**What to add:**
- Company policies (refund, privacy, terms of service)
- Email templates (welcome, follow-up, proposal, rejection)
- Product information
- Service descriptions
- Pricing information
- Company background and mission
- Process documentation
- Best practices and guidelines

**doc_type options:**
- `policy` - Company policies
- `email_template` - Email templates
- `proposal_template` - Proposal templates
- `faq` - FAQ content (or use the `faqs` table)
- `general` - General business info

**category examples:**
- `customer_service`, `sales`, `support`, `onboarding`, `billing`, `technical`, `company`

### 👥 Contacts Table

**What to add:**
- Clients (current customers)
- Prospects (potential customers)
- Partners (referral partners, vendors)
- Internal team members (if needed)

**relationship_type options:**
- `client` - Current customer
- `prospect` - Potential customer
- `partner` - Business partner
- `vendor` - Service provider
- `internal` - Team member

### 📄 Proposals Table

**What to add:**
- Proposal templates (with `is_template = true`)
- Sent proposals (with `is_template = false`)

**Use placeholders in templates:**
- `[CLIENT_NAME]`
- `[PROJECT_NAME]`
- `[AMOUNT]`
- `[DATE]`

The agent will fill these in when drafting.

### ❓ FAQs Table

**What to add:**
- Common customer questions
- Internal process questions
- Technical questions
- Billing questions

**Tips:**
- Add good keywords for better search
- Keep answers concise but complete
- Organize by category

## Ongoing Maintenance

### Adding New Data

**Option 1: Via Script**
```bash
python scripts/ingest_business_data.py --json new_data.json
```

**Option 2: Via Supabase UI**
- Go to Table Editor
- Select table
- Click "Insert row"

**Option 3: Via API (from your app)**
The agent can add data programmatically using the `rag_cli.py` tool.

### Updating Existing Data

1. Go to Supabase Table Editor
2. Find the row you want to update
3. Click the row to edit
4. Make changes
5. The `updated_at` timestamp will auto-update

### Backing Up Your Data

**Option 1: Supabase Backups (Automatic)**
- Supabase automatically backs up your database daily
- Available in Project Settings > Database > Backups

**Option 2: Manual Export**
```bash
# Export to JSON
supabase db dump > backup.sql
```

## Troubleshooting

### "No results found" when searching

**Possible causes:**
1. No data ingested yet → Run `--sample` first
2. Embeddings not generated → Check that `OPENAI_API_KEY` is set
3. Search threshold too high → Try lowering it in the query

### "Connection error" when running scripts

**Possible causes:**
1. Wrong Supabase URL → Check `.env` file
2. Wrong API key → Make sure you're using `SUPABASE_SERVICE_KEY`, not `SUPABASE_KEY`
3. Network issue → Check your internet connection

### "Permission denied" errors

**Cause:** Using the `anon` key instead of `service_role` key

**Solution:** Make sure `.env` has:
```bash
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## Advanced: Email Context Caching (Optional)

The schema includes tables for caching email threads and messages. This is optional but recommended for faster performance.

**To enable:**
1. The agent will automatically cache emails as it processes them
2. This reduces API calls to Gmail
3. Provides faster search across your email history

**Tables:**
- `email_threads` - Thread-level metadata
- `email_messages` - Individual messages

## Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use service_role key only in backend** - Never expose it in frontend code
3. **Enable Row Level Security (RLS)** if you have multiple users
4. **Rotate keys periodically** - Generate new keys in Supabase settings

## Next Steps

Once your Supabase is set up:

1. ✅ Test the RAG system: `python tools/rag_cli.py search --query "test"`
2. ✅ Run the agent locally: `uvicorn src.main:app --reload`
3. ✅ Test the `/api/text` endpoint with a question about your business
4. ✅ Deploy to Google Cloud Run (see `DEPLOYMENT.md`)

---

**Need help?** Check the main README.md or open an issue on GitHub.
