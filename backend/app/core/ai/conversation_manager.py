"""
Conversation Manager - Multi-turn conversation support
Manages conversation sessions, query history, and context for follow-up queries
"""
#backend/app/core/ai/conversation_manager.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """Single message in a conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get recent messages"""
        return self.messages[-limit:]
    
    def get_context_summary(self) -> str:
        """Generate a summary of conversation context"""
        if not self.messages:
            return "No conversation history"
        
        summary_parts = []
        
        # Add recent queries
        user_messages = [m for m in self.messages if m.role == MessageRole.USER]
        if user_messages:
            recent_queries = [m.content for m in user_messages[-3:]]
            summary_parts.append(f"Recent queries: {', '.join(recent_queries)}")
        
        # Add context items
        if self.context:
            context_items = [f"{k}: {v}" for k, v in self.context.items() if k != "dataframe"]
            if context_items:
                summary_parts.append(f"Context: {', '.join(context_items[:5])}")
        
        return " | ".join(summary_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": {k: v for k, v in self.context.items() if k != "dataframe"},  # Exclude DataFrame
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.messages)
        }


class ConversationManager:
    """Manage conversation sessions and context"""
    
    def __init__(
        self,
        max_history: int = 50,
        session_timeout_minutes: int = 30
    ):
        """
        Initialize conversation manager
        
        Args:
            max_history: Maximum messages to keep per session
            session_timeout_minutes: Session timeout in minutes
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_history = max_history
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # In-memory session storage (can be replaced with Redis/MongoDB)
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """
        Create a new conversation session
        
        Args:
            session_id: Optional custom session ID
        
        Returns:
            New ConversationSession
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = ConversationSession(session_id=session_id)
        self.sessions[session_id] = session
        
        self.logger.info(f"Created conversation session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get existing session or None
        
        Args:
            session_id: Session ID
        
        Returns:
            ConversationSession or None
        """
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session has timed out
            if datetime.now() - session.last_activity > self.session_timeout:
                self.logger.info(f"Session {session_id} has timed out")
                self.delete_session(session_id)
                return None
        
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """
        Get existing session or create new one
        
        Args:
            session_id: Optional session ID
        
        Returns:
            ConversationSession
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(session_id)
    
    def add_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add user message to session"""
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.USER, content, metadata)
        self._trim_history(session)
    
    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add assistant message to session"""
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.ASSISTANT, content, metadata)
        self._trim_history(session)
    
    def update_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ):
        """
        Update session context
        
        Args:
            session_id: Session ID
            context_updates: Dictionary of context updates
        """
        session = self.get_or_create_session(session_id)
        session.context.update(context_updates)
        session.last_activity = datetime.now()
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        session = self.get_session(session_id)
        return session.context if session else {}
    
    def resolve_references(
        self,
        session_id: str,
        query: str
    ) -> str:
        """
        Resolve pronouns and references in query using conversation context
        
        Args:
            session_id: Session ID
            query: User query with potential references
        
        Returns:
            Query with resolved references
        """
        session = self.get_session(session_id)
        if not session or not session.messages:
            return query
        
        query_lower = query.lower()
        resolved_query = query
        
        # Get last mentioned entities from context
        last_chart_type = session.context.get("last_chart_type")
        last_columns = session.context.get("last_columns", [])
        last_filters = session.context.get("last_filters", {})
        
        # Resolve "it", "that", "this"
        if any(word in query_lower for word in ["it", "that", "this"]):
            if last_chart_type:
                resolved_query = resolved_query.replace("it", last_chart_type)
                resolved_query = resolved_query.replace("that", last_chart_type)
                resolved_query = resolved_query.replace("this", last_chart_type)
        
        # Resolve "same" (e.g., "show me the same for Q4")
        if "same" in query_lower and last_columns:
            # Add context about what "same" refers to
            context_hint = f" (referring to: {', '.join(last_columns)})"
            resolved_query += context_hint
        
        # Resolve "previous", "last"
        if any(word in query_lower for word in ["previous", "last"]) and session.messages:
            user_messages = [m for m in session.messages if m.role == MessageRole.USER]
            if len(user_messages) > 1:
                last_query = user_messages[-2].content
                context_hint = f" (previous query was: {last_query})"
                resolved_query += context_hint
        
        return resolved_query
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history as list of dictionaries
        
        Args:
            session_id: Session ID
            limit: Optional limit on number of messages
        
        Returns:
            List of message dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.get_recent_messages(limit) if limit else session.messages
        return [m.to_dict() for m in messages]
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > self.session_timeout
        ]
        
        for sid in expired:
            self.delete_session(sid)
        
        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def _trim_history(self, session: ConversationSession):
        """Trim message history to max_history"""
        if len(session.messages) > self.max_history:
            # Keep only recent messages
            session.messages = session.messages[-self.max_history:]
    
    def get_session_summary(self, session_id: str) -> Optional[str]:
        """Get a summary of the session"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.get_context_summary()
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return [
            {
                "session_id": sid,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            }
            for sid, session in self.sessions.items()
        ]


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
