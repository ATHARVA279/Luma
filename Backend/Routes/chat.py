from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from Services.gemini_client import ask_question_about_text
from Services.persistent_vector_store import PersistentVectorStore
from Middleware.auth import get_current_user
from Middleware.rate_limit import limit_chat
from Services.chat_utils import get_general_response


router = APIRouter()

from models.requests import ChatRequest

@router.post("/chat", dependencies=[Depends(limit_chat)])
async def chat_with_document(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    question = (req.question or "").strip()
    history = req.history or []
    user_id = current_user['uid']

    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    try:
        response = get_general_response(question)
        if response:
            return {
                "answer": response,
                "sources_used": 0
            }
        
        store = PersistentVectorStore()
        
        results = await store.search_bm25(user_id, question, k=req.top_k, document_id=req.document_id)
        
        if not results:
            return {
                "answer": "I don't have information about that in the loaded content. Please ask questions related to the document you extracted, or extract new content from the Home page.",
                "sources_used": 0
            }
        
        context_chunks = [r["content"] for r in results]
        context = "\n\n".join(context_chunks)
        
        history_text = ""
        if history:
            recent_history = history[-4:]
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
        
        answer = ask_question_about_text(question, context, history=history)
        
        return {
            "answer": answer,
            "sources_used": len(context_chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
