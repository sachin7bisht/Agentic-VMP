# ==========================================
# File: src/domain/models.py
# ==========================================
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

class Vendor(BaseModel):
    """
    Represents a row in the 'vendors' SQL table.
    """
    id: int
    vendor_id_str: str = Field(..., description="The CSV Vendor ID (e.g., V7755)")
    name: str = Field(..., description="Company Name")
    contact_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    category: str = "General"
    status: str = "Active"
    
class Invoice(BaseModel):
    """
    Represents a row in the 'invoices' SQL table.
    """
    id: int
    vendor_id: int
    invoice_number: str
    amount: float
    currency: str = "USD"
    status: str
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    created_at: Optional[datetime] = None

class ConversationRow(BaseModel):
    """
    Represents a historical message row from 'conversation_history'.
    """
    id: Optional[int] = None
    session_id: str
    thread_id: str
    role: str  # 'user' or 'assistant'
    content: str
    created_at: Optional[datetime] = None