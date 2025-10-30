# Backend/Services/conversational_memory.py
"""
Conversational Memory using LangChain for context-aware chat
Maintains conversation history and handles follow-up questions
"""
import os
from typing import List, Dict, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
import json

# In-memory session storage (in production, use Redis or database)
_sessions = {}

class ConversationSession:
    """Manages a single conversation session with memory"""
    
    def __init__(self, session_id: str, k: int = 10):
        """
        Initialize conversation session
        k: number of message pairs to remember (default 10 = 20 messages)
        """
        self.session_id = session_id
        self.memory = ConversationBufferWindowMemory(
            k=k,
            return_messages=True,
            memory_key="chat_history"
        )
        self.metadata = {
            "created_at": None,
            "last_active": None,
            "message_count": 0,
            "topics_discussed": []
        }
    
    def add_message(self, human_message: str, ai_message: str):
        """Add a conversation exchange to memory"""
        self.memory.save_context(
            {"input": human_message},
            {"output": ai_message}
        )
        self.metadata["message_count"] += 1
        self.metadata["last_active"] = self._get_timestamp()
    
    def get_history(self) -> List[Dict]:
        """Get conversation history as list of dicts"""
        messages = self.memory.load_memory_variables({}).get("chat_history", [])
        
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    def get_context_string(self) -> str:
        """Get conversation history as formatted string for LLM context"""
        history = self.get_history()
        
        if not history:
            return "No previous conversation."
        
        context_parts = ["Previous conversation:"]
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        self.metadata["message_count"] = 0
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_summary(self) -> Dict:
        """Get session summary"""
        return {
            "session_id": self.session_id,
            "message_count": self.metadata["message_count"],
            "last_active": self.metadata["last_active"],
            "history_length": len(self.get_history())
        }

def get_or_create_session(session_id: str, memory_window: int = 10) -> ConversationSession:
    """Get existing session or create new one"""
    if session_id not in _sessions:
        _sessions[session_id] = ConversationSession(session_id, k=memory_window)
    return _sessions[session_id]

def add_conversation_exchange(session_id: str, user_message: str, ai_response: str):
    """Add a conversation exchange to session"""
    session = get_or_create_session(session_id)
    session.add_message(user_message, ai_response)

def get_conversation_history(session_id: str) -> List[Dict]:
    """Get conversation history for session"""
    if session_id not in _sessions:
        return []
    return _sessions[session_id].get_history()

def get_conversation_context(session_id: str) -> str:
    """Get formatted conversation context for LLM"""
    if session_id not in _sessions:
        return "No previous conversation."
    return _sessions[session_id].get_context_string()

def clear_session(session_id: str):
    """Clear a session's memory"""
    if session_id in _sessions:
        _sessions[session_id].clear_memory()

def delete_session(session_id: str):
    """Delete a session completely"""
    if session_id in _sessions:
        del _sessions[session_id]

def get_active_sessions() -> List[Dict]:
    """Get list of all active sessions"""
    return [session.get_summary() for session in _sessions.values()]

def get_session_summary(session_id: str) -> Optional[Dict]:
    """Get summary of specific session"""
    if session_id in _sessions:
        return _sessions[session_id].get_summary()
    return None

# Context-aware query enhancement
def enhance_query_with_context(query: str, session_id: str) -> str:
    """
    Enhance query with conversation context for better retrieval
    Handles pronouns and follow-up questions
    """
    if session_id not in _sessions:
        return query
    
    history = _sessions[session_id].get_history()
    
    if not history:
        return query
    
    # Get last few messages for context
    recent_messages = history[-4:] if len(history) > 4 else history
    
    # Check if query is a follow-up (short, has pronouns, etc.)
    is_followup = (
        len(query.split()) < 5 or
        any(word in query.lower() for word in ['it', 'this', 'that', 'they', 'them', 'its'])
    )
    
    if is_followup and len(recent_messages) >= 2:
        # Add context from previous exchange
        context = " ".join([msg["content"] for msg in recent_messages[-2:]])
        enhanced_query = f"{context} {query}"
        return enhanced_query
    
    return query
