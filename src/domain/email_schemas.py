# ==========================================
# File: src/domain/email_schemas.py
# ==========================================
from pydantic import BaseModel, Field, EmailStr

class EmailInput(BaseModel):
    """
    Represents the structure of an incoming email event.
    """
    id: str = Field(..., description="Unique message identifier from the email provider")
    thread_id: str = Field(..., description="Conversation identifier for grouping messages")
    sender: EmailStr = Field(..., description="Email address of the sender (Verified by SecurityNode)")
    subject: str = Field(..., description="Subject line of the email")
    body: str = Field(..., description="Plain text body content of the email")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "thread_id": "thread_abc",
                "sender": "supplier@acme.com",
                "subject": "Invoice Status INV-2024",
                "body": "Hi, can you check the status of invoice INV-2024?"
            }
        }

class AgentOutput(BaseModel):
    """
    Represents the final result of the agent's execution.
    """
    generated_email: str = Field(..., description="The draft response content")
    action_taken: str = Field(..., description="Summary of actions (e.g., 'Checked Status', 'Updated Vendor')")
    is_authorized: bool = Field(..., description="Whether the request passed security checks")