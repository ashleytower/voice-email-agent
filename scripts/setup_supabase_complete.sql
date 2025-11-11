-- Complete Supabase Schema for Voice-First AI Email Agent
-- This schema stores ALL business knowledge: FAQs, proposals, contacts, email context, etc.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. KNOWLEDGE BASE (RAG) - Core documents with vector embeddings
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    doc_type TEXT,  -- 'faq', 'proposal_template', 'policy', 'email_template', 'general'
    category TEXT,  -- e.g., 'sales', 'support', 'refunds', 'onboarding'
    title TEXT,
    source TEXT,  -- Original file path or URL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Indexes for filtering
CREATE INDEX IF NOT EXISTS documents_doc_type_idx ON documents(doc_type);
CREATE INDEX IF NOT EXISTS documents_category_idx ON documents(category);

-- Vector similarity search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    filter_doc_type TEXT DEFAULT NULL,
    filter_category TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    doc_type TEXT,
    category TEXT,
    title TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        documents.doc_type,
        documents.category,
        documents.title,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE 
        (1 - (documents.embedding <=> query_embedding) > match_threshold)
        AND (filter_doc_type IS NULL OR documents.doc_type = filter_doc_type)
        AND (filter_category IS NULL OR documents.category = filter_category)
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- 2. CONTACTS - Business contacts with relationship context
-- ============================================================================

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    company TEXT,
    role TEXT,
    phone TEXT,
    relationship_type TEXT,  -- 'client', 'prospect', 'partner', 'vendor', 'internal'
    status TEXT DEFAULT 'active',  -- 'active', 'inactive', 'archived'
    notes TEXT,
    metadata JSONB DEFAULT '{}',  -- Custom fields
    last_contact_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contacts_email_idx ON contacts(email);
CREATE INDEX IF NOT EXISTS contacts_company_idx ON contacts(company);
CREATE INDEX IF NOT EXISTS contacts_relationship_type_idx ON contacts(relationship_type);

-- ============================================================================
-- 3. PROPOSALS - Proposal templates and sent proposals
-- ============================================================================

CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_template BOOLEAN DEFAULT false,
    template_name TEXT,  -- If this is a template
    contact_id UUID REFERENCES contacts(id),
    status TEXT DEFAULT 'draft',  -- 'draft', 'sent', 'accepted', 'rejected'
    sent_date TIMESTAMP WITH TIME ZONE,
    value DECIMAL(10, 2),  -- Proposal value
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS proposals_contact_id_idx ON proposals(contact_id);
CREATE INDEX IF NOT EXISTS proposals_is_template_idx ON proposals(is_template);
CREATE INDEX IF NOT EXISTS proposals_status_idx ON proposals(status);

-- ============================================================================
-- 4. EMAIL THREADS - Cached email context for fast retrieval
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id TEXT UNIQUE NOT NULL,  -- Gmail thread ID
    subject TEXT,
    participants TEXT[],  -- Array of email addresses
    last_message_date TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 1,
    labels TEXT[],  -- Gmail labels
    summary TEXT,  -- AI-generated summary
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS email_threads_thread_id_idx ON email_threads(thread_id);
CREATE INDEX IF NOT EXISTS email_threads_participants_idx ON email_threads USING GIN(participants);

-- ============================================================================
-- 5. EMAIL MESSAGES - Individual messages within threads
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id TEXT UNIQUE NOT NULL,  -- Gmail message ID
    thread_id TEXT REFERENCES email_threads(thread_id),
    from_email TEXT,
    to_emails TEXT[],
    cc_emails TEXT[],
    subject TEXT,
    body TEXT,
    snippet TEXT,
    date TIMESTAMP WITH TIME ZONE,
    labels TEXT[],
    has_attachments BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS email_messages_message_id_idx ON email_messages(message_id);
CREATE INDEX IF NOT EXISTS email_messages_thread_id_idx ON email_messages(thread_id);
CREATE INDEX IF NOT EXISTS email_messages_from_email_idx ON email_messages(from_email);

-- ============================================================================
-- 6. USER PREFERENCES - User-specific settings and writing style
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT UNIQUE NOT NULL,
    writing_style JSONB DEFAULT '{}',  -- Learned writing patterns
    preferences JSONB DEFAULT '{}',  -- General preferences
    signature TEXT,
    default_labels TEXT[],
    notification_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_preferences_user_email_idx ON user_preferences(user_email);

-- ============================================================================
-- 7. FAQ CATEGORIES - Organized FAQ structure
-- ============================================================================

CREATE TABLE IF NOT EXISTS faq_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_category_id UUID REFERENCES faq_categories(id),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES faq_categories(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT[],
    usage_count INTEGER DEFAULT 0,  -- Track how often this FAQ is retrieved
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS faqs_category_id_idx ON faqs(category_id);
CREATE INDEX IF NOT EXISTS faqs_keywords_idx ON faqs USING GIN(keywords);

-- ============================================================================
-- TRIGGERS - Auto-update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_threads_updated_at BEFORE UPDATE ON email_threads
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faqs_updated_at BEFORE UPDATE ON faqs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- View: Recent email activity by contact
CREATE OR REPLACE VIEW contact_email_activity AS
SELECT 
    c.id as contact_id,
    c.name,
    c.email,
    c.company,
    COUNT(em.id) as email_count,
    MAX(em.date) as last_email_date
FROM contacts c
LEFT JOIN email_messages em ON em.from_email = c.email OR c.email = ANY(em.to_emails)
GROUP BY c.id, c.name, c.email, c.company;

-- View: Proposal pipeline summary
CREATE OR REPLACE VIEW proposal_pipeline AS
SELECT 
    status,
    COUNT(*) as count,
    SUM(value) as total_value,
    AVG(value) as avg_value
FROM proposals
WHERE is_template = false
GROUP BY status;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE documents IS 'Core knowledge base with vector embeddings for RAG';
COMMENT ON TABLE contacts IS 'Business contacts with relationship context';
COMMENT ON TABLE proposals IS 'Proposal templates and sent proposals';
COMMENT ON TABLE email_threads IS 'Cached email thread metadata for fast retrieval';
COMMENT ON TABLE email_messages IS 'Individual email messages';
COMMENT ON TABLE user_preferences IS 'User-specific settings and learned writing style';
COMMENT ON TABLE faqs IS 'Frequently asked questions with usage tracking';
