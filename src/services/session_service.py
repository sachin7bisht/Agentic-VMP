# ==========================================
# File: src/services/session_service.py
# ==========================================
import logging
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.core.db_manager import db_manager
from src.domain.models import ConversationRow
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

class SessionService:
    """
    Manages conversation history in SQL.
    Translates between SQL rows and LangChain Message objects.
    """

    def log_message(self, session_id: str, thread_id: str, role: str, content: str):
        """
        Saves a single message to the database.
        
        Args:
            role: 'user' (Vendor) or 'assistant' (AI)
        """
        query = """
            INSERT INTO conversation_history (session_id, thread_id, role, content)
            VALUES (?, ?, ?, ?)
        """
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (session_id, thread_id, role, content))
        except Exception as e:
            logger.error(f"Failed to log message for thread {thread_id}: {e}")

    def get_chat_history(self, thread_id: str, limit: int = 5) -> List[BaseMessage]:
        """
        Retrieves the last N messages for a thread, formatted for the LLM.
        
        Returns:
            List[BaseMessage]: A list of HumanMessage/AIMessage objects.
        """
        # Get the N most recent messages
        query = """
            SELECT role, content 
            FROM conversation_history 
            WHERE thread_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        
        messages: List[BaseMessage] = []
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (thread_id, limit))
                rows = cursor.fetchall()
                
                # SQL returns [Newest, ..., Oldest]. 
                # We need [Oldest, ..., Newest] for the LLM context window.
                for row in reversed(rows):
                    role = row['role']
                    content = row['content']
                    
                    if role == 'user':
                        messages.append(HumanMessage(content=content))
                    elif role == 'assistant':
                        messages.append(AIMessage(content=content))
                        
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving history for thread {thread_id}: {e}")
            return []

# Singleton Instance
session_service = SessionService()