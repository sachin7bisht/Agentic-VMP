# ==========================================
# File: src/common/exceptions.py
# ==========================================
import sys
import traceback
from typing import Optional, cast

class UnifiedAgentException(Exception):
    """
    Custom exception class that captures standard python exception details,
    formats the traceback, and prepares a logger-friendly string.
    
    Source: Provided exceptions.py
    """
    def __init__(self, error_message, error_details: Optional[object] = None):
        # Normalize message
        if isinstance(error_message, BaseException):
            norm_msg = str(error_message)
        else:
            norm_msg = str(error_message)

        # Resolve exc_info (supports: sys module, Exception object, or current context)
        exc_type = exc_value = exc_tb = None
        if error_details is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        else:
            if hasattr(error_details, "exc_info"):  # e.g., sys
                # casting to Any or explicit type to satisfy static analysis
                exc_info_obj = cast(sys, error_details) # type: ignore
                exc_type, exc_value, exc_tb = exc_info_obj.exc_info()
            elif isinstance(error_details, BaseException):
                exc_type, exc_value, exc_tb = type(error_details), error_details, error_details.__traceback__
            else:
                exc_type, exc_value, exc_tb = sys.exc_info()

        # Walk to the last frame to report the most relevant location
        last_tb = exc_tb
        while last_tb and last_tb.tb_next:
            last_tb = last_tb.tb_next

        self.file_name = last_tb.tb_frame.f_code.co_filename if last_tb else "<unknown>"
        self.lineno = last_tb.tb_lineno if last_tb else -1
        self.error_message = norm_msg

        # Full pretty traceback (if available)
        if exc_type and exc_tb:
            self.traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        else:
            self.traceback_str = ""

        super().__init__(self.__str__())

    def __str__(self):
        # Compact, logger-friendly message (no leading spaces)
        base = f"Error in [{self.file_name}] at line [{self.lineno}] | Message: {self.error_message}"
        if self.traceback_str:
            return f"{base}\nTraceback:\n{self.traceback_str}"
        return base

    def __repr__(self):
        return f"UnifiedAgentException(file={self.file_name!r}, line={self.lineno}, message={self.error_message!r})"

# --- Domain Specific Exceptions ---
# These inherit from UnifiedAgentException to get the detailed logging capabilities

class VendorAgentException(UnifiedAgentException):
    """Base domain exception for the Agent workflow."""
    pass

class SecurityException(VendorAgentException):
    """Raised when a security violation or unauthorized access is detected."""
    pass

class ConfigurationException(VendorAgentException):
    """Raised when critical settings or API keys are missing."""
    pass

class ValidationException(VendorAgentException):
    """Raised when user input (email, phone, intent) fails validation rules."""
    pass

class LLMGenerationException(VendorAgentException):
    """Raised when the LLM fails to produce a valid response or hallucinates."""
    pass

class DatabaseException(VendorAgentException):
    """Raised when SQL operations fail (connections, constraints)."""
    pass

class ResourceNotFoundException(VendorAgentException):
    """Raised when a requested entity (Invoice, Vendor) is not found."""
    pass