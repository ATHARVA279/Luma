# Backend/Routes/advanced_chat.py
"""
Advanced chat with conversational memory and hybrid RAG
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from Services.gemini_client import ask_question_about_text
from Services import advanced_rag_service as rag
from Services import conversational_memory as memory

router = APIRouter()

class AdvancedChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    search_method: Optional[str] = "hybrid"  # hybrid, rrf, tfidf, bm25
    top_k: int = 4
    use_memory: bool = True

@router.post("/chat/advanced")
def advanced_chat(req: AdvancedChatRequest):
    """
    Advanced RAG-powered chat with:
    - Conversational memory
    - Hybrid search (TF-IDF + BM25)
    - Context-aware query enhancement
    """
    question = (req.question or "").strip()
    session_id = req.session_id or "default"
    
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    
    try:
        # Check for conversational responses
        general_responses = {
            "ok": "Feel free to ask me anything about the content!",
            "okay": "What else would you like to know?",
            "thanks": "You're welcome! Ask me anything else.",
            "thank you": "Happy to help! Any other questions?",
            "got it": "Great! What else can I help you with?",
            "alright": "Is there anything else you'd like to know?",
        }
        
        if question.lower() in general_responses:
            response = general_responses[question.lower()]
            if req.use_memory:
                memory.add_conversation_exchange(session_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "search_method": "none",
                "session_id": session_id
            }
        
        # Enhance query with conversation context
        enhanced_query = question
        if req.use_memory:
            enhanced_query = memory.enhance_query_with_context(question, session_id)
        
        # Retrieve context using selected method
        if req.search_method == "rrf":
            context_results = rag.reciprocal_rank_fusion(enhanced_query, k=req.top_k)
        else:
            context_results = rag.hybrid_search(enhanced_query, k=req.top_k)
        
        if not context_results:
            response = "I don't have information about that in the loaded content. Please extract text from a URL first on the Home page."
            if req.use_memory:
                memory.add_conversation_exchange(session_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "session_id": session_id
            }
        
        # Combine contexts
        context = "\n\n".join([r["content"] for r in context_results])
        
        # Get conversation history for context
        conversation_context = ""
        if req.use_memory:
            conversation_context = memory.get_conversation_context(session_id)
        
        # Build enhanced prompt with conversation context
        if conversation_context and conversation_context != "No previous conversation.":
            enhanced_prompt = f"""{conversation_context}

Current question: {question}

Relevant content from documents:
{context}

Answer the current question using the provided content and conversation context."""
            answer = ask_question_about_text(question, enhanced_prompt, history=[])
        else:
            answer = ask_question_about_text(question, context, history=[])
        
        # Save to memory
        if req.use_memory:
            memory.add_conversation_exchange(session_id, question, answer)
        
        return {
            "answer": answer,
            "sources_used": len(context_results),
            "search_method": req.search_method,
            "search_scores": [{"score": r["score"], "source": r["source"]} for r in context_results],
            "session_id": session_id,
            "query_enhanced": enhanced_query != question
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/chat/history/{session_id}")
def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    history = memory.get_conversation_history(session_id)
    summary = memory.get_session_summary(session_id)
    
    return {
        "session_id": session_id,
        "history": history,
        "summary": summary
    }

@router.delete("/chat/session/{session_id}")
def clear_chat_session(session_id: str):
    """Clear a chat session"""
    memory.clear_session(session_id)
    return {"message": f"Session {session_id} cleared", "session_id": session_id}

@router.get("/chat/sessions")
def list_active_sessions():
    """Get all active chat sessions"""
    sessions = memory.get_active_sessions()
    return {"sessions": sessions, "total": len(sessions)}
