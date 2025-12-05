import os
from typing import List, Dict, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
import json

_sessions = {}

class ConversationSession:
    
    def __init__(self, session_id: str, user_id: str, k: int = 10):
        self.session_id = session_id
        self.user_id = user_id
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
        self.memory.save_context(
            {"input": human_message},
            {"output": ai_message}
        )
        self.metadata["message_count"] += 1
        self.metadata["last_active"] = self._get_timestamp()
    
    def get_history(self) -> List[Dict]:
        messages = self.memory.load_memory_variables({}).get("chat_history", [])
        
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    def get_context_string(self) -> str:
        history = self.get_history()
        
        if not history:
            return "No previous conversation."
        
        context_parts = ["Previous conversation:"]
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_memory(self):
        self.memory.clear()
        self.metadata["message_count"] = 0
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_summary(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message_count": self.metadata["message_count"],
            "last_active": self.metadata["last_active"],
            "history_length": len(self.get_history())
        }

def get_or_create_session(session_id: str, user_id: str, memory_window: int = 10) -> ConversationSession:
    if session_id in _sessions:
        session = _sessions[session_id]
        if session.user_id != user_id:
            raise PermissionError(f"Session {session_id} belongs to another user")
        return session
    
    session = ConversationSession(session_id, user_id, k=memory_window)
    _sessions[session_id] = session
    return session

def add_conversation_exchange(session_id: str, user_id: str, user_message: str, ai_response: str):
    try:
        session = get_or_create_session(session_id, user_id)
        session.add_message(user_message, ai_response)
    except PermissionError:
        pass

def get_conversation_history(session_id: str, user_id: str) -> List[Dict]:
    if session_id not in _sessions:
        return []
    
    session = _sessions[session_id]
    if session.user_id != user_id:
        return []
        
    return session.get_history()

def get_conversation_context(session_id: str, user_id: str) -> str:
    if session_id not in _sessions:
        return "No previous conversation."
    
    session = _sessions[session_id]
    if session.user_id != user_id:
        return "No previous conversation."
        
    return session.get_context_string()

def clear_session(session_id: str, user_id: str):
    if session_id in _sessions:
        session = _sessions[session_id]
        if session.user_id == user_id:
            session.clear_memory()

def delete_session(session_id: str, user_id: str):
    if session_id in _sessions:
        session = _sessions[session_id]
        if session.user_id == user_id:
            del _sessions[session_id]

def get_active_sessions(user_id: str) -> List[Dict]:
    return [
        session.get_summary() 
        for session in _sessions.values() 
        if session.user_id == user_id
    ]

def get_session_summary(session_id: str, user_id: str) -> Optional[Dict]:
    if session_id in _sessions:
        session = _sessions[session_id]
        if session.user_id == user_id:
            return session.get_summary()
    return None

def enhance_query_with_context(query: str, session_id: str, user_id: str) -> str:
    if session_id not in _sessions:
        return query
    
    session = _sessions[session_id]
    if session.user_id != user_id:
        return query
    
    history = session.get_history()
    
    if not history:
        return query
    
    recent_messages = history[-4:] if len(history) > 4 else history
    
    is_followup = (
        len(query.split()) < 5 or
        any(word in query.lower() for word in ['it', 'this', 'that', 'they', 'them', 'its'])
    )
    
    if is_followup and len(recent_messages) >= 2:
        context = " ".join([msg["content"] for msg in recent_messages[-2:]])
        enhanced_query = f"{context} {query}"
        return enhanced_query
    
    return query
