from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from Services.gemini_client import ask_question_about_text
from Services.persistent_vector_store import PersistentVectorStore
from Services import conversational_memory as memory
from Middleware.auth import get_current_user
from Middleware.rate_limit import limit_chat
from Services.chat_utils import get_general_response

router = APIRouter()

from models.requests import AdvancedChatRequest

@router.post("/chat/advanced", dependencies=[Depends(limit_chat)])
async def advanced_chat(req: AdvancedChatRequest, current_user: dict = Depends(get_current_user)):
    question = (req.question or "").strip()
    session_id = req.session_id or "default"
    user_id = current_user['uid']
    
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    
    try:
        response = get_general_response(question)
        if response:
            if req.use_memory:
                memory.add_conversation_exchange(session_id, user_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "search_method": "none",
                "session_id": session_id
            }
        
        enhanced_query = question
        if req.use_memory:
            enhanced_query = memory.enhance_query_with_context(question, session_id, user_id)
        
        from Services.credit_service import CreditService
        await CreditService.check_and_deduct(current_user['uid'], "chat")

        store = PersistentVectorStore()
        
        context_results = await store.search_bm25(user_id, enhanced_query, k=req.top_k, document_id=req.document_id)
        
        if not context_results:
            response = "I don't have information about that in the loaded content. Please extract text from a URL first on the Home page."
            if req.use_memory:
                memory.add_conversation_exchange(session_id, user_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "session_id": session_id
            }
        
        context = "\n\n".join([r["content"] for r in context_results])
        
        conversation_context = ""
        if req.use_memory:
            conversation_context = memory.get_conversation_context(session_id, user_id)
        
        if conversation_context and conversation_context != "No previous conversation.":
            enhanced_prompt = f"""{conversation_context}

Current question: {question}

Relevant content from documents:
{context}

Answer the current question using the provided content and conversation context."""
            answer = ask_question_about_text(question, enhanced_prompt, history=[])
        else:
            answer = ask_question_about_text(question, context, history=[])
        
        if req.use_memory:
            memory.add_conversation_exchange(session_id, user_id, question, answer)
        
        return {
            "answer": answer,
            "sources_used": len(context_results),
            "search_method": req.search_method,
            "search_scores": [{"score": r["score"], "source": "db"} for r in context_results],
            "session_id": session_id,
            "query_enhanced": enhanced_query != question
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/chat/history/{session_id}")
def get_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    history = memory.get_conversation_history(session_id, current_user['uid'])
    summary = memory.get_session_summary(session_id, current_user['uid'])
    
    return {
        "session_id": session_id,
        "history": history,
        "summary": summary
    }

@router.delete("/chat/session/{session_id}")
def clear_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    memory.clear_session(session_id, current_user['uid'])
    return {"message": f"Session {session_id} cleared", "session_id": session_id}

@router.get("/chat/sessions")
def list_active_sessions(current_user: dict = Depends(get_current_user)):
    sessions = memory.get_active_sessions(current_user['uid'])
    return {"sessions": sessions, "total": len(sessions)}
