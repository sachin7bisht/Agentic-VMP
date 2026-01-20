# ==========================================
# File: src/graph/nodes/save_node.py
# ==========================================
import logging
from src.domain.state import GraphState
from src.services.session_service import session_service
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

def save_conversation(state: GraphState) -> GraphState:
    """
    Graph Node: Persists the interaction to the SQL database.
    
    Logic:
    1. Log the User's input email.
    2. Log the AI's generated response.
    """
    logger.info("--- NODE: Save Conversation ---")
    
    email = state["email_input"]
    generated_reply = state.get("generated_email")
    
    # 1. Save User Message
    session_service.log_message(
        session_id=email.thread_id, # Using thread_id as session_id for simplicity
        thread_id=email.thread_id,
        role="user",
        content=email.body
    )
    
    # 2. Save AI Response (if one exists)
    if generated_reply:
        session_service.log_message(
            session_id=email.thread_id,
            thread_id=email.thread_id,
            role="assistant",
            content=generated_reply
        )
        logger.info(f"Saved interaction for thread: {email.thread_id}")
        
    return {
        "final_action": "Conversation Saved"
    }