# ==========================================
# File: src/graph/nodes/executor_nodes.py
# ==========================================
import logging
from langchain_core.messages import SystemMessage

from src.domain.state import GraphState
from src.services.vendor_service import vendor_service
from src.services.rag_service import rag_service
from src.services.data_loader import data_loader # Import DataLoader
from src.core.llm_factory import LLMFactory
from config.logging_config import GLOBAL_LOGGER as logger
from config.prompt_templates import EXTRACTION_SYSTEM_PROMPT


def _extract_entity(history: list, query: str) -> str:
    """Helper: Uses LLM to extract specific data."""
    llm = LLMFactory.get_llm(temperature=0.0)
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        SystemMessage(content=f"Extract: {query}")
    ] + history
    return llm.invoke(messages).content.strip().replace("'", "").replace('"', "")

# ------------------------------------------------------------------------------
# Node 1: Execute Status Check (Full Data Context)
# ------------------------------------------------------------------------------

def execute_status(state: GraphState) -> GraphState:
    """
    Graph Node: Fetches Invoice AND Vendor data.
    Combines all columns from ledger_data.csv into the context.
    """
    log = logger.bind(node="execute_status")
    
    vendor = state["vendor_details"]
    history = state["messages"]
    
    invoice_number = _extract_entity(history, "The Invoice Number (e.g., INV-123) mentioned by the user.")
    
    if "NOT_FOUND" in invoice_number:
         # Fallback for "Pending Invoices" query
        pending_list = vendor_service.get_pending_invoices(vendor.id)
        if pending_list:
            summary = "\n".join([f"- {inv['invoice_number']}: {inv['amount']} {inv['currency']} (Due: {inv['due_date']})" for inv in pending_list])
            result = f"Here are your pending invoices:\n{summary}"
        else:
            result = "I could not identify a specific invoice, and you have no pending invoices."
    else:
        log.info("fetching_invoice_data", invoice=invoice_number)
        invoice_data = vendor_service.get_invoice_status(invoice_number, vendor.id)
        
        if invoice_data:
            # 2. Construct the "Full Context" string with ALL columns
            # This matches the structure of ledger_data.csv exactly
            result = (
                f"--- INVOICE DETAILS ---\n"
                f"Invoice ID: {invoice_data.get('invoice_number')}\n"
                f"Amount: {invoice_data.get('amount')} {invoice_data.get('currency')}\n"
                f"Status: {invoice_data.get('status')}\n"
                f"Due Date: {invoice_data.get('due_date')}\n"
                f"Invoice Date (Issue): {invoice_data.get('issue_date')}\n\n"
                f"--- VENDOR PROFILE (Source: Ledger) ---\n"
                f"Vendor ID: {vendor.vendor_id_str}\n"
                f"Company: {vendor.name}\n"
                f"Contact Name: {vendor.contact_name}\n"
                f"Email: {vendor.email}\n"
                f"Phone: {vendor.phone}\n"
                f"Address: {vendor.address}\n"
                f"Role/Category: {vendor.category}"
            )
        else:
            result = f"Invoice {invoice_number} not found in our records."

    return {
        "sql_results": result,
        "final_action": f"Checked Status for {invoice_number}"
    }

# ------------------------------------------------------------------------------
# Node 2: Execute Update
# ------------------------------------------------------------------------------
def execute_update(state: GraphState) -> GraphState:
    """
    Graph Node: Updates vendor contact info in SQL AND Syncs to CSV.
    """
    log = logger.bind(node="execute_update")
    vendor = state["vendor_details"]
    history = state["messages"]

    extraction_prompt = "Extract the field to update (phone/address/contact_name) and the new value. Format: 'FIELD:VALUE'"
    extracted = _extract_entity(history, extraction_prompt)
    
    try:
        if ":" not in extracted:
            raise ValueError("Could not parse update request.")
            
        field, value = extracted.split(":", 1)
        field = field.lower().strip()
        value = value.strip()
        
        # Validation
        from src.common.utils import Validators
        if field == "phone":
            clean_phone = Validators.sanitize_phone_number(value)
            if not clean_phone:
                return {"sql_results": f"Update Rejected: Phone number '{value}' invalid."}
            value = clean_phone
            
        # 1. Update SQL Database
        result = vendor_service.update_vendor_contact(vendor.id, field, value)
        
        # 2. NEW: If successful, Sync changes back to CSV
        if "Successfully updated" in result:
            data_loader.sync_db_to_csv()
            log.info("triggered_csv_sync")
        
    except Exception as e:
        log.warning("update_parsing_failed", error=str(e))
        result = "I could not clarify what you want to update. Please specify Field and Value."

    return {
        "sql_results": result,
        "final_action": "Attempted Profile Update"
    }

# ------------------------------------------------------------------------------
# Node 3: Execute RAG (Policy Search)
# ------------------------------------------------------------------------------

def execute_policy(state: GraphState) -> GraphState:
    """
    Graph Node: Retrieves policy documents from Vector Store.
    """
    log = logger.bind(node="execute_policy")
    log.info("executing_policy_retrieval")
    query = state["email_input"].body
    context_chunks = rag_service.retrieve_policy_context(query)
    return {
        "rag_chunks": context_chunks,
        "final_action": "Retrieved Policy Context"
    }