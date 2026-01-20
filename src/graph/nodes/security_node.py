# ==========================================
# File: src/graph/nodes/security_node.py
# ==========================================
from config.logging_config import GLOBAL_LOGGER as logger
from src.domain.state import GraphState
from src.services.auth_service import auth_service
from config.settings import settings

def security_check(state: GraphState) -> GraphState:
    """
    Graph Node: Validates the sender's email against the Vendor Master.
    
    Logic:
    1. Extract sender email from input.
    2. Query SQL DB via AuthService.
    3. Update state with authorization status and vendor details.
    """
    email_input = state["email_input"]
    sender_email = email_input.sender.lower().strip()
    
    # CHANGED: Bind node context
    log = logger.bind(node="security_node", email=sender_email)
    log.info("executing_node")
    
    vendor = auth_service.verify_vendor(sender_email)
    
    if vendor:
        log.info("security_check_passed", vendor_id=vendor.id)
        return {
            "is_authorized": True,
            "vendor_details": vendor,
            "final_action": "Security Check Passed"
        }
    else:
        log.warning("security_check_failed")
        return {
            "is_authorized": False,
            "vendor_details": None,
            "final_action": "Security Check Failed"
        }