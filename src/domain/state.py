# ==========================================
# File: src/domain/state.py
# ==========================================
from typing import Annotated, List, Optional, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from src.domain.email_schemas import EmailInput
from src.domain.models import Vendor

class GraphState(TypedDict):
    """
    Represents the state of the agent workflow.
    This dictionary is passed and modified between every node in the graph.
    """
    
    # --- Input Data ---
    email_input: EmailInput  # The raw incoming email payload
    
    # --- Security & Context ---
    is_authorized: bool      # Result of SecurityNode
    vendor_details: Optional[Vendor] # Populated if authorized
    
    # --- Chat History (LLM Context) ---
    # 'add_messages' ensures new messages are appended to the list, not overwritten
    messages: Annotated[List[BaseMessage], add_messages]
    
    # --- Classification ---
    # Categories: 'UPDATE', 'STATUS', 'POLICY', 'UNRELATED'
    intent: str
    
    # --- Execution Results (Hybrid Layer) ---
    sql_results: Optional[str]   # Output from Vendor/Invoice queries
    rag_chunks: Optional[str]    # Retrieved text from Policy PDF
    
    # --- Final Output ---
    generated_email: str     # The draft response
    final_action: str        # Debug/Audit string of what happened
    
    # --- Control Flow ---
    error_message: Optional[str] # If something goes wrong (e.g., SQL failure)