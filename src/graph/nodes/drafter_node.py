# ==========================================
# File: src/graph/nodes/drafter_node.py
# ==========================================
import logging
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser

from src.core.llm_factory import LLMFactory
from src.domain.state import GraphState
from config.prompt_templates import DRAFTER_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

def draft_response(state: GraphState) -> GraphState:
    """
    Graph Node: Generates the final email response using the gathered data.
    
    Logic:
    1. Select the relevant data source based on intent (SQL vs RAG).
    2. Format the DRAFTER_SYSTEM_PROMPT.
    3. Invoke LLM to write the email.
    """
    logger.info("--- NODE: Drafter ---")
    
    intent = state.get("intent", "UNRELATED")
    vendor = state.get("vendor_details")
    vendor_name = vendor.name if vendor else "Vendor"
    
    # 1. Determine which data context to use
    data_context = ""
    if intent in ["STATUS", "UPDATE"]:
        data_context = state.get("sql_results") or "Action completed, but no specific details returned."
    elif intent == "POLICY":
        data_context = state.get("rag_chunks") or "No relevant policy documents found."
    else:
        data_context = "User asked something unrelated to Invoices or Policies."

    # 2. Prepare Prompt
    # We format the system prompt with the specific variables
    system_instruction = DRAFTER_SYSTEM_PROMPT.format(
        vendor_name=vendor_name,
        intent=intent,
        data_context=data_context
    )
    
    # 3. Invoke LLM
    # We use a slightly higher temperature (0.3) for better writing flow
    llm = LLMFactory.get_llm(temperature=0.3)
    
    messages = [SystemMessage(content=system_instruction)] + state["messages"]
    
    chain = llm | StrOutputParser()
    response = chain.invoke(messages)
    
    logger.info("Draft generated successfully.")
    
    return {
        "generated_email": response,
        "final_action": "Drafted Response"
    }

def rejection_response(state: GraphState) -> GraphState:
    """
    Graph Node: Generates a security rejection email.
    Called when SecurityNode returns is_authorized=False.
    """
    logger.info("--- NODE: Rejection Drafter ---")
    
    # Hardcoded rejection for security reasons (no LLM tokens wasted)
    rejection_msg = (
        "Dear Sender,\n\n"
        "We could not verify your email address in our Vendor Master database. "
        "For security reasons, we cannot process your request.\n\n"
        "Please contact support@agentia.com if you believe this is an error.\n\n"
        "Best regards,\nAgentia Security Team"
    )
    
    return {
        "generated_email": rejection_msg,
        "final_action": "Sent Rejection Email"
    }