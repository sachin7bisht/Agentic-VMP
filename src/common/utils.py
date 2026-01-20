# ==========================================
# File: src/common/utils.py
# ==========================================
import re
import logging
from typing import Optional

logger = logging.getLogger("common_utils")

class Validators:
    """
    Static utility class for common validation patterns.
    """

    @staticmethod
    def sanitize_phone_number(phone: str) -> Optional[str]:
        """
        Removes all non-digit characters from a phone string.
        Returns None if the result is invalid (e.g., too short).
        
        Args:
            phone (str): Input string (e.g., "(555) 123-4567")
        
        Returns:
            str: "5551234567" or None
        """
        if not phone:
            return None
            
        # Remove anything that is not a digit
        clean_number = re.sub(r'\D', '', phone)
        
        # Simple constraint: standard US numbers are 10 digits
        if len(clean_number) < 10:
            logger.warning(f"Phone validation failed for input: {phone}")
            return None
            
        return clean_number

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Checks if the string matches standard email format.
        Note: Pydantic 'EmailStr' handles this in models, but this 
        is useful for runtime checks in services.
        """
        # Simple robust regex for emails
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return bool(re.match(email_regex, email))

    @staticmethod
    def extract_invoice_number(text: str) -> Optional[str]:
        """
        Attempts to find an Invoice ID pattern (e.g., INV-2024-001) in text.
        Useful as a fallback if the LLM fails to extract it.
        """
        # Looks for "INV-" followed by alphanumerics/dashes
        match = re.search(r'(INV-[A-Za-z0-9-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

class Formatters:
    """
    Static utility class for display formatting.
    """
    
    @staticmethod
    def currency(amount: float, currency_code: str = "USD") -> str:
        """
        Formats float to currency string (e.g., $1,200.50).
        """
        return f"{amount:,.2f} {currency_code}"