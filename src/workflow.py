"""
LangGraph Workflow - Deterministic State Machine for Email Agent

This module implements the core orchestration logic using LangGraph's StateGraph.
It replaces the unreliable LLM instruction-following with a deterministic workflow.
"""
import json
import subprocess
from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# Define the state structure
class AgentState(TypedDict):
    """State maintained throughout the workflow."""
    user_input: str
    intent: Literal["DRAFT_EMAIL", "RETRIEVE_INFO", "MANAGE_INBOX", "READ_EMAIL", "UNKNOWN"]
    context: dict
    draft: str
    final_response: str
    error: str


# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)


def classify_intent(state: AgentState) -> AgentState:
    """
    Classify user intent using LLM.
    This is the ONLY place where LLM is used for decision-making,
    and the output is strictly constrained to one of the defined intents.
    """
    user_input = state["user_input"]
    
    system_prompt = """You are an intent classifier for an AI email agent.
    
Classify the user's request into ONE of these intents:
- DRAFT_EMAIL: User wants to compose, write, or send an email
- RETRIEVE_INFO: User wants to search for information, ask a question, or retrieve knowledge
- MANAGE_INBOX: User wants to label, archive, organize, or manage emails
- READ_EMAIL: User wants to read, listen to, or review specific emails
- UNKNOWN: The request doesn't fit any category

Respond with ONLY the intent name, nothing else."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User request: {user_input}")
    ]
    
    response = llm.invoke(messages)
    intent = response.content.strip()
    
    # Validate intent
    valid_intents = ["DRAFT_EMAIL", "RETRIEVE_INFO", "MANAGE_INBOX", "READ_EMAIL", "UNKNOWN"]
    if intent not in valid_intents:
        intent = "UNKNOWN"
    
    state["intent"] = intent
    return state


def route_by_intent(state: AgentState) -> str:
    """Route to the appropriate handler based on classified intent."""
    intent = state["intent"]
    
    if intent == "DRAFT_EMAIL":
        return "draft_email"
    elif intent == "RETRIEVE_INFO":
        return "retrieve_info"
    elif intent == "MANAGE_INBOX":
        return "manage_inbox"
    elif intent == "READ_EMAIL":
        return "read_email"
    else:
        return "handle_unknown"


def draft_email(state: AgentState) -> AgentState:
    """Handle email drafting workflow."""
    user_input = state["user_input"]
    
    # Step 1: Search RAG for relevant templates/context
    rag_result = subprocess.run(
        ["python", "tools/rag_cli.py", "search", "--query", user_input, "--limit", "3"],
        capture_output=True,
        text=True
    )
    
    rag_data = json.loads(rag_result.stdout) if rag_result.returncode == 0 else {"results": []}
    
    # Step 2: Use LLM to generate draft with RAG context
    context_text = "\n\n".join([r["content"] for r in rag_data.get("results", [])])
    
    system_prompt = f"""You are an email drafting assistant.

User request: {user_input}

Relevant context from knowledge base:
{context_text}

Draft a professional email based on the user's request and the provided context.
Include appropriate subject line and body."""
    
    messages = [SystemMessage(content=system_prompt)]
    response = llm.invoke(messages)
    
    state["draft"] = response.content
    state["final_response"] = f"I've drafted an email for you:\n\n{response.content}\n\nWould you like me to send it or make changes?"
    
    return state


def retrieve_info(state: AgentState) -> AgentState:
    """Handle information retrieval from RAG."""
    user_input = state["user_input"]
    
    # Search RAG knowledge base
    rag_result = subprocess.run(
        ["python", "tools/rag_cli.py", "search", "--query", user_input, "--limit", "5"],
        capture_output=True,
        text=True
    )
    
    rag_data = json.loads(rag_result.stdout) if rag_result.returncode == 0 else {"results": []}
    
    if rag_data.get("results"):
        # Use LLM to synthesize answer from results
        context_text = "\n\n".join([f"- {r['content']}" for r in rag_data["results"]])
        
        system_prompt = f"""You are a helpful assistant with access to the company knowledge base.

User question: {user_input}

Relevant information from knowledge base:
{context_text}

Provide a clear, concise answer to the user's question based on this information."""
        
        messages = [SystemMessage(content=system_prompt)]
        response = llm.invoke(messages)
        
        state["final_response"] = response.content
    else:
        state["final_response"] = "I couldn't find relevant information in the knowledge base for that question."
    
    return state


def manage_inbox(state: AgentState) -> AgentState:
    """Handle inbox management tasks (label, archive, etc.)."""
    user_input = state["user_input"]
    
    # Use LLM to extract action and parameters
    system_prompt = f"""Extract the email management action from this request: "{user_input}"

Respond in JSON format:
{{
  "action": "label" or "archive",
  "message_id": "extracted message ID if mentioned",
  "label_name": "label name if action is label"
}}"""
    
    messages = [SystemMessage(content=system_prompt)]
    response = llm.invoke(messages)
    
    try:
        action_data = json.loads(response.content)
        action = action_data.get("action")
        message_id = action_data.get("message_id")
        
        if not message_id:
            # Try to get the latest email
            list_result = subprocess.run(
                ["python", "tools/email_cli.py", "list", "--query", "", "--max-results", "1"],
                capture_output=True,
                text=True
            )
            list_data = json.loads(list_result.stdout)
            if list_data.get("emails"):
                message_id = list_data["emails"][0]["id"]
        
        if action == "label":
            label_name = action_data.get("label_name", "Important")
            result = subprocess.run(
                ["python", "tools/email_cli.py", "label", "--message-id", message_id, "--label", label_name],
                capture_output=True,
                text=True
            )
            state["final_response"] = f"I've labeled the email with '{label_name}'."
        
        elif action == "archive":
            result = subprocess.run(
                ["python", "tools/email_cli.py", "archive", "--message-id", message_id],
                capture_output=True,
                text=True
            )
            state["final_response"] = "I've archived the email."
        
        else:
            state["final_response"] = "I'm not sure how to handle that inbox management request."
    
    except Exception as e:
        state["error"] = str(e)
        state["final_response"] = "I encountered an error while managing your inbox."
    
    return state


def read_email(state: AgentState) -> AgentState:
    """Handle reading emails aloud."""
    user_input = state["user_input"]
    
    # Get recent emails
    list_result = subprocess.run(
        ["python", "tools/email_cli.py", "list", "--query", "is:unread", "--max-results", "5"],
        capture_output=True,
        text=True
    )
    
    list_data = json.loads(list_result.stdout) if list_result.returncode == 0 else {"emails": []}
    
    if list_data.get("emails"):
        # Summarize the emails
        email_summaries = []
        for email in list_data["emails"][:3]:
            email_summaries.append(f"From {email['from']}: {email['subject']}")
        
        summary_text = "\n".join(email_summaries)
        state["final_response"] = f"Here are your recent unread emails:\n\n{summary_text}"
    else:
        state["final_response"] = "You have no unread emails."
    
    return state


def handle_unknown(state: AgentState) -> AgentState:
    """Handle unknown or unclear intents."""
    state["final_response"] = "I'm not sure how to help with that. Could you rephrase your request?"
    return state


# Build the workflow graph
def create_workflow() -> StateGraph:
    """Create and return the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("draft_email", draft_email)
    workflow.add_node("retrieve_info", retrieve_info)
    workflow.add_node("manage_inbox", manage_inbox)
    workflow.add_node("read_email", read_email)
    workflow.add_node("handle_unknown", handle_unknown)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "draft_email": "draft_email",
            "retrieve_info": "retrieve_info",
            "manage_inbox": "manage_inbox",
            "read_email": "read_email",
            "handle_unknown": "handle_unknown"
        }
    )
    
    # All handlers go to END
    workflow.add_edge("draft_email", END)
    workflow.add_edge("retrieve_info", END)
    workflow.add_edge("manage_inbox", END)
    workflow.add_edge("read_email", END)
    workflow.add_edge("handle_unknown", END)
    
    return workflow.compile()


# Create the compiled workflow
agent_workflow = create_workflow()


def process_user_input(user_input: str) -> str:
    """
    Process user input through the workflow and return the final response.
    
    Args:
        user_input: The user's voice command (transcribed text)
    
    Returns:
        The agent's text response (to be converted to speech)
    """
    initial_state = {
        "user_input": user_input,
        "intent": "UNKNOWN",
        "context": {},
        "draft": "",
        "final_response": "",
        "error": ""
    }
    
    result = agent_workflow.invoke(initial_state)
    return result["final_response"]
