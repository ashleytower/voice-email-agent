#!/usr/bin/env python3
"""
Email CLI Tool - MCP-Optimized Gmail Operations

This tool provides CLI commands for all Gmail operations using direct Gmail API access,
following the Code Execution with MCP pattern for maximum token efficiency.

Usage:
    python email_cli.py send --to "user@example.com" --subject "Hello" --body "Message"
    python email_cli.py list --query "is:unread" --max-results 10
    python email_cli.py get --message-id "abc123"
    python email_cli.py label --message-id "abc123" --label "Important"
    python email_cli.py archive --message-id "abc123"
"""
import argparse
import json
import sys
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_gmail_service():
    """Initialize and return Gmail API service."""
    # Use OAuth refresh token to get credentials
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Gmail OAuth credentials not configured")
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    return build('gmail', 'v1', credentials=creds)


def send_email(to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Dict[str, Any]:
    """Send an email via Gmail API."""
    try:
        service = get_gmail_service()
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        msg = MIMEText(body)
        message.attach(msg)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "status": "success",
            "message_id": result['id'],
            "thread_id": result['threadId']
        }
    except HttpError as error:
        return {"status": "error", "message": f"Gmail API error: {error}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_emails(query: str = "", max_results: int = 10) -> Dict[str, Any]:
    """List emails matching a query."""
    try:
        service = get_gmail_service()
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        email_list = []
        for msg in messages:
            # Get full message details
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
            
            email_list.append({
                "id": msg['id'],
                "thread_id": msg['threadId'],
                "from": headers.get('From', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "snippet": full_msg.get('snippet', '')
            })
        
        return {"status": "success", "emails": email_list, "count": len(email_list)}
    except HttpError as error:
        return {"status": "error", "message": f"Gmail API error: {error}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_email(message_id: str) -> Dict[str, Any]:
    """Get full email details by message ID."""
    try:
        service = get_gmail_service()
        
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode()
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode()
        
        return {
            "status": "success",
            "email": {
                "id": message['id'],
                "thread_id": message['threadId'],
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "body": body,
                "labels": message.get('labelIds', [])
            }
        }
    except HttpError as error:
        return {"status": "error", "message": f"Gmail API error: {error}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def label_email(message_id: str, label: str) -> Dict[str, Any]:
    """Add a label to an email."""
    try:
        service = get_gmail_service()
        
        # Get or create label
        labels = service.users().labels().list(userId='me').execute()
        label_id = None
        
        for lbl in labels.get('labels', []):
            if lbl['name'].lower() == label.lower():
                label_id = lbl['id']
                break
        
        if not label_id:
            # Create new label
            label_object = {
                'name': label,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            label_id = created_label['id']
        
        # Add label to message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        
        return {"status": "success", "label_id": label_id}
    except HttpError as error:
        return {"status": "error", "message": f"Gmail API error: {error}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def archive_email(message_id: str) -> Dict[str, Any]:
    """Archive an email (remove from inbox)."""
    try:
        service = get_gmail_service()
        
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        
        return {"status": "success"}
    except HttpError as error:
        return {"status": "error", "message": f"Gmail API error: {error}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Email CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send an email")
    send_parser.add_argument("--to", required=True, help="Recipient email address")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--cc", help="CC email addresses (comma-separated)")
    send_parser.add_argument("--bcc", help="BCC email addresses (comma-separated)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List emails")
    list_parser.add_argument("--query", default="", help="Gmail search query")
    list_parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get email details")
    get_parser.add_argument("--message-id", required=True, help="Message ID")
    
    # Label command
    label_parser = subparsers.add_parser("label", help="Add label to email")
    label_parser.add_argument("--message-id", required=True, help="Message ID")
    label_parser.add_argument("--label", required=True, help="Label name")
    
    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive an email")
    archive_parser.add_argument("--message-id", required=True, help="Message ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    result = {}
    if args.command == "send":
        result = send_email(args.to, args.subject, args.body, args.cc, args.bcc)
    elif args.command == "list":
        result = list_emails(args.query, args.max_results)
    elif args.command == "get":
        result = get_email(args.message_id)
    elif args.command == "label":
        result = label_email(args.message_id, args.label)
    elif args.command == "archive":
        result = archive_email(args.message_id)
    
    # Output result as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
