# ==========================================
# File: src/services/auth_service.py
# ==========================================
from typing import Optional
from src.core.db_manager import db_manager
from src.domain.models import Vendor
from config.settings import settings
from config.logging_config import GLOBAL_LOGGER as logger


class AuthService:
    """
    Service responsible for verifying vendor identity.
    acts as the 'Gatekeeper' for the AI Agent.
    """
    
    def verify_vendor(self, sender_email: str) -> Optional[Vendor]:
        """
        Checks if the email belongs to an authorized vendor in the SQL database.
        
        Args:
            sender_email (str): The email address extracted from the incoming message.
            
        Returns:
            Optional[Vendor]: A Vendor model if found, None otherwise.
        """
        log = logger.bind(service="AuthService", email=sender_email)
        
        query = "SELECT * FROM vendors WHERE email = ? LIMIT 1"
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (sender_email,))
                row = cursor.fetchone()
                
                if row:
                    vendor = Vendor(**dict(row))
                    # CHANGED: specific event logging
                    log.info("access_granted", vendor_name=vendor.name)
                    return vendor
                else:
                    log.warning("access_denied")
                    return None
                    
        except Exception as e:
            log.error("auth_check_error", error=str(e))
            return None

auth_service = AuthService()