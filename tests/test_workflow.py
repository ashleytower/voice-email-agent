"""
Test Suite for Voice-First AI Email Agent Workflow

This module implements Test-Driven Development (TDD) tests for the core workflow.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow import process_user_input, classify_intent, AgentState


class TestIntentClassification:
    """Test intent classification logic."""
    
    def test_draft_email_intent(self):
        """Test that draft email requests are correctly classified."""
        state = {
            "user_input": "Draft a proposal email for Acme Corp about our new product",
            "intent": "UNKNOWN",
            "context": {},
            "draft": "",
            "final_response": "",
            "error": ""
        }
        
        result = classify_intent(state)
        assert result["intent"] == "DRAFT_EMAIL"
    
    def test_retrieve_info_intent(self):
        """Test that information retrieval requests are correctly classified."""
        state = {
            "user_input": "What is our refund policy?",
            "intent": "UNKNOWN",
            "context": {},
            "draft": "",
            "final_response": "",
            "error": ""
        }
        
        result = classify_intent(state)
        assert result["intent"] == "RETRIEVE_INFO"
    
    def test_manage_inbox_intent(self):
        """Test that inbox management requests are correctly classified."""
        state = {
            "user_input": "Label the last email as important and archive it",
            "intent": "UNKNOWN",
            "context": {},
            "draft": "",
            "final_response": "",
            "error": ""
        }
        
        result = classify_intent(state)
        assert result["intent"] == "MANAGE_INBOX"
    
    def test_read_email_intent(self):
        """Test that read email requests are correctly classified."""
        state = {
            "user_input": "Read me the subject lines of my unread emails",
            "intent": "UNKNOWN",
            "context": {},
            "draft": "",
            "final_response": "",
            "error": ""
        }
        
        result = classify_intent(state)
        assert result["intent"] == "READ_EMAIL"


class TestWorkflowEndToEnd:
    """Test end-to-end workflow execution."""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not configured"
    )
    def test_draft_email_workflow(self):
        """Test TDD-1: Draft email workflow."""
        user_input = "Draft a proposal email for Acme Corp about our consulting services"
        
        response = process_user_input(user_input)
        
        assert response is not None
        assert len(response) > 0
        assert "email" in response.lower() or "draft" in response.lower()
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or not os.getenv("SUPABASE_URL"),
        reason="API keys not configured"
    )
    def test_retrieve_info_workflow(self):
        """Test TDD-2: Information retrieval workflow."""
        user_input = "What is our refund policy?"
        
        response = process_user_input(user_input)
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or not os.getenv("GMAIL_CLIENT_ID"),
        reason="API keys not configured"
    )
    def test_manage_inbox_workflow(self):
        """Test TDD-3: Inbox management workflow."""
        user_input = "Label the last email as Important"
        
        response = process_user_input(user_input)
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or not os.getenv("GMAIL_CLIENT_ID"),
        reason="API keys not configured"
    )
    def test_read_email_workflow(self):
        """Test TDD-4: Read email workflow."""
        user_input = "Read me the subject lines of my unread emails"
        
        response = process_user_input(user_input)
        
        assert response is not None
        assert len(response) > 0


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_input(self):
        """Test handling of empty user input."""
        response = process_user_input("")
        
        assert response is not None
        # Should handle gracefully, not crash
    
    def test_very_long_input(self):
        """Test handling of very long user input."""
        long_input = "Tell me about " + ("our products " * 1000)
        
        response = process_user_input(long_input)
        
        assert response is not None
        # Should handle gracefully, not crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
