# ==========================================
# File: src/graph/edges.py
# ==========================================
from typing import Literal
from src.domain.state import GraphState

def route_security(state: GraphState) -> Literal["load_memory", "rejection_response"]:
    """
    Router: Checks if the user passed the SecurityNode.
    """
    if state.get("is_authorized"):
        return "load_memory"
    return "rejection_response"

def route_intent(state: GraphState) -> Literal["execute_status", "execute_update", "execute_policy", "draft_response"]:
    """
    Router: Directs the flow based on the Classifier's output.
    """
    intent = state.get("intent")
    
    if intent == "STATUS":
        return "execute_status"
    elif intent == "UPDATE":
        return "execute_update"
    elif intent == "POLICY":
        return "execute_policy"
    
    # "UNRELATED" or unknown intents go straight to drafting a polite "I can't help" email
    return "draft_response"