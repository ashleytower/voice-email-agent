# Deployment Guide: Voice-First AI Email Agent

This guide provides step-by-step instructions for deploying the AI email agent to Google Cloud Run.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Cloud CLI** installed and authenticated
3. **Docker** installed locally (for testing)
4. **Supabase Project** set up with the schema from `scripts/setup_supabase.sql`
5. **API Keys** for OpenAI, Gmail, and Google Cloud services

## Step 1: Configure Supabase

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Run the SQL schema setup:
   ```bash
   # Copy the contents of scripts/setup_supabase.sql
   # Paste into Supabase SQL Editor and execute
   ```
3. Note your Supabase URL and service key

## Step 2: Set Up Google Cloud APIs

1. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable speech.googleapis.com
   gcloud services enable texttospeech.googleapis.com
   gcloud services enable gmail.googleapis.com
   ```

2. Create a service account for Google Cloud APIs:
   ```bash
   gcloud iam service-accounts create email-agent-sa \
       --display-name="Email Agent Service Account"
   
   gcloud iam service-accounts keys create service-account-key.json \
       --iam-account=email-agent-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

## Step 3: Configure Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 Client ID (Desktop app)
4. Download the credentials
5. Run the OAuth flow to get a refresh token:
   ```python
   # Use the google-auth-oauthlib library to get refresh token
   # Save the refresh token for deployment
   ```

## Step 4: Build and Test Locally

1. Create a `.env` file with all credentials:
   ```bash
   cp .env.example .env
   # Fill in all the values
   ```

2. Build the Docker image:
   ```bash
   docker build -t voice-email-agent .
   ```

3. Run locally:
   ```bash
   docker run -p 8000:8000 --env-file .env voice-email-agent
   ```

4. Test the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

## Step 5: Deploy to Google Cloud Run

1. Set your project ID:
   ```bash
   export PROJECT_ID=your-project-id
   gcloud config set project $PROJECT_ID
   ```

2. Build and push the container:
   ```bash
   gcloud builds submit --tag gcr.io/$PROJECT_ID/voice-email-agent
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy voice-email-agent \
       --image gcr.io/$PROJECT_ID/voice-email-agent \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --set-env-vars="ENVIRONMENT=production" \
       --set-secrets="OPENAI_API_KEY=openai-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_SERVICE_KEY=supabase-key:latest,GMAIL_CLIENT_ID=gmail-client-id:latest,GMAIL_CLIENT_SECRET=gmail-client-secret:latest,GMAIL_REFRESH_TOKEN=gmail-refresh-token:latest,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,SENTRY_DSN=sentry-dsn:latest" \
       --memory 2Gi \
       --cpu 2 \
       --timeout 300 \
       --max-instances 10
   ```

   **Note:** Secrets should be created in Google Secret Manager first:
   ```bash
   echo -n "your-openai-key" | gcloud secrets create openai-key --data-file=-
   echo -n "your-supabase-url" | gcloud secrets create supabase-url --data-file=-
   # Repeat for all secrets
   ```

4. Get the service URL:
   ```bash
   gcloud run services describe voice-email-agent \
       --platform managed \
       --region us-central1 \
       --format 'value(status.url)'
   ```

## Step 6: Ingest Business Data

1. Prepare your business data (FAQs, templates, policies) in text files
2. Run the ingestion script:
   ```bash
   python scripts/ingest_data.py --data-dir /path/to/your/business/data
   ```
   
   Or ingest sample data:
   ```bash
   python scripts/ingest_data.py --sample
   ```

## Step 7: Test the Deployed Service

1. Test the health endpoint:
   ```bash
   curl https://your-service-url.run.app/health
   ```

2. Test the text endpoint:
   ```bash
   curl -X POST https://your-service-url.run.app/api/text \
       -H "Content-Type: application/json" \
       -d '{"text": "What is our refund policy?"}'
   ```

3. Test the WebSocket endpoint (use a WebSocket client or the web app)

## Monitoring and Maintenance

### View Logs
```bash
gcloud run services logs read voice-email-agent \
    --platform managed \
    --region us-central1
```

### Update the Service
```bash
# Make code changes, then:
gcloud builds submit --tag gcr.io/$PROJECT_ID/voice-email-agent
gcloud run deploy voice-email-agent \
    --image gcr.io/$PROJECT_ID/voice-email-agent \
    --platform managed \
    --region us-central1
```

### Scale Configuration
```bash
# Adjust min/max instances
gcloud run services update voice-email-agent \
    --min-instances 1 \
    --max-instances 20 \
    --platform managed \
    --region us-central1
```

## Troubleshooting

### Issue: Container fails to start
- Check logs: `gcloud run services logs read voice-email-agent`
- Verify all environment variables are set correctly
- Ensure all secrets are accessible

### Issue: API calls failing
- Verify API keys are correct
- Check that all required Google Cloud APIs are enabled
- Ensure service account has necessary permissions

### Issue: High latency
- Increase CPU/memory allocation
- Enable Cloud CDN for static assets
- Optimize the number of Cloud Run instances

## Security Best Practices

1. **Use Secret Manager** for all sensitive credentials
2. **Enable VPC** for private Supabase connections
3. **Implement rate limiting** on the API endpoints
4. **Use Cloud Armor** for DDoS protection
5. **Enable Cloud Audit Logs** for compliance

## Cost Optimization

1. Set appropriate min/max instances
2. Use request-based pricing (pay per use)
3. Monitor usage with Cloud Monitoring
4. Set up budget alerts

## Next Steps

1. Build a web client for the WebSocket interface
2. Implement user authentication
3. Add more sophisticated RAG strategies
4. Integrate with additional email providers
5. Add support for attachments and rich media

For support, please refer to the main README.md or open an issue on GitHub.
