# ==========================================
# File: src/services/vendor_service.py
# ==========================================
import logging
from typing import Optional, Dict, Any, Union, List
from src.core.db_manager import db_manager
from config.settings import settings

# Use structured logger
from config.logging_config import GLOBAL_LOGGER as logger

class VendorService:
    """
    Handles business logic for Vendor operations.
    """

    def get_invoice_status(self, invoice_number: str, vendor_id: int) -> Union[str, Dict[str, Any]]:
        """
        Retrieves the FULL details of a specific invoice.
        Returns a dictionary of the row so the Executor can format it.
        """
        # Fetch everything (SELECT *) to ensure we have dates, amounts, etc.
        query = "SELECT * FROM invoices WHERE invoice_number = ? AND vendor_id = ?"
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (invoice_number, vendor_id))
                row = cursor.fetchone()
                
                if row:
                    # Convert sqlite3.Row to a standard Python dict
                    return dict(row)
                else:
                    return None
                    
        except Exception as e:
            logger.error("error_fetching_invoice", error=str(e))
            return None

    def get_pending_invoices(self, vendor_id: int) -> List[Dict[str, Any]]:
        """
        Restored Function: Returns all pending invoices for the vendor.
        Useful for "What do I owe?" queries.
        """
        query = "SELECT * FROM invoices WHERE vendor_id = ? AND status = 'Pending'"
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (vendor_id,))
                rows = cursor.fetchall()
                
                # Convert list of Rows to list of Dicts
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error("error_fetching_pending", error=str(e))
            return []

    def update_vendor_contact(self, vendor_id: int, field: str, value: str) -> str:
        """
        Updates a specific contact field for the vendor.
        """
        ALLOWED_FIELDS = {'phone', 'name', 'category', 'address', 'contact_name'}
        
        if field not in ALLOWED_FIELDS:
            return f"Error: Updating field '{field}' is not permitted."
            
        query = f"UPDATE vendors SET {field} = ? WHERE id = ?"
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (value, vendor_id))
                
                if cursor.rowcount > 0:
                    logger.info("vendor_updated", vendor_id=vendor_id, field=field)
                    return f"Successfully updated your {field} to '{value}'."
                else:
                    return "Update failed. Vendor record not found."
                    
        except Exception as e:
            logger.error("error_updating_vendor", error=str(e))
            return "System error during update."

# Singleton Instance
vendor_service = VendorService()