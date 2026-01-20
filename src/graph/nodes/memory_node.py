# ==========================================
# File: src/graph/nodes/memory_node.py
# ==========================================
import logging
from langchain_core.messages import HumanMessage

from src.domain.state import GraphState
from src.services.session_service import session_service
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

def load_memory(state: GraphState) -> GraphState:
    """
    Graph Node: Loads recent conversation history from SQL.
    
    Logic:
    1. Identify the thread_id from the email input.
    2. Fetch the last 5 messages via SessionService.
    3. Append the *current* email as a new HumanMessage to the context.
    """
    logger.info("--- NODE: Load Memory ---")
    
    email_input = state["email_input"]
    thread_id = email_input.thread_id
    current_message_content = email_input.body
    
    # 1. Fetch historical context (from SQL)
    history = session_service.get_chat_history(thread_id, limit=5)
    
    # 2. Add the CURRENT incoming email to the list
    # Note: We don't save to SQL here; we save at the End/SaveNode. 
    # Here we just prepare the context for the LLM.
    current_message = HumanMessage(content=current_message_content)
    
    # Combine history + current message
    # The 'add_messages' reducer in GraphState will handle merging this list
    full_context = history + [current_message]
    
    logger.info(f"Loaded {len(history)} historical messages for Thread ID: {thread_id}")
    
    return {
        "messages": full_context
    }