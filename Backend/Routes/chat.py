from fastapi import APIRouter, HTTPException, Depends
from Services.gemini_client import ask_question_about_text
from Services.persistent_vector_store import PersistentVectorStore
from Services.conversational_memory import ChatSessionService
from Middleware.auth import get_current_user
from Middleware.rate_limit import limit_chat
from Services.chat_utils import get_general_response
from Services.credit_service import CreditService
from models.requests import ChatRequest

router = APIRouter()


@router.post("/chat", dependencies=[Depends(limit_chat)])
async def chat_with_document(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    question = (req.question or "").strip()
    document_id = req.document_id
    user_id = current_user['uid']
    
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required for chat")
    
    try:
        response = get_general_response(question)
        if response:
            await ChatSessionService.add_exchange(user_id, document_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "document_id": document_id
            }
        
        enhanced_query = await ChatSessionService.enhance_query(question, user_id, document_id)
        
        transaction_id = await CreditService.check_and_deduct(user_id, "chat")
        
        store = PersistentVectorStore()
        context_results = await store.search_bm25(
            user_id, 
            enhanced_query, 
            k=req.top_k, 
            document_id=document_id
        )
        
        if not context_results:
            response = "I don't have information about that in this document. Please make sure you've extracted content from it first."
            await ChatSessionService.add_exchange(user_id, document_id, question, response)
            return {
                "answer": response,
                "sources_used": 0,
                "document_id": document_id
            }
        
        context = "\n\n".join([r["content"] for r in context_results])
        
        conversation_context = await ChatSessionService.get_context_string(user_id, document_id)
        
        if conversation_context and conversation_context != "No previous conversation.":
            enhanced_prompt = f"""{conversation_context}

Current question: {question}

Relevant content from document:
{context}

Answer the current question using the provided content and conversation context."""
            answer = ask_question_about_text(question, enhanced_prompt, history=[])
        else:
            answer = ask_question_about_text(question, context, history=[])
        
        await ChatSessionService.add_exchange(user_id, document_id, question, answer)
        
        await CreditService.complete_transaction(user_id, transaction_id)
        
        return {
            "answer": answer,
            "sources_used": len(context_results),
            "document_id": document_id,
            "query_enhanced": enhanced_query != question
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat/history/{document_id}")
async def get_chat_history(document_id: str, current_user: dict = Depends(get_current_user)):
    """Get chat history for a specific document."""
    user_id = current_user['uid']
    history = await ChatSessionService.get_history(user_id, document_id)
    summary = await ChatSessionService.get_session_summary(user_id, document_id)
    
    return {
        "document_id": document_id,
        "history": history,
        "summary": summary
    }


@router.delete("/chat/session/{document_id}")
async def clear_chat_session(document_id: str, current_user: dict = Depends(get_current_user)):
    """Clear all chat messages for a specific document."""
    user_id = current_user['uid']
    await ChatSessionService.clear_session(user_id, document_id)
    return {"message": f"Chat for document {document_id} cleared", "document_id": document_id}


@router.get("/chat/sessions")
async def list_chat_sessions(current_user: dict = Depends(get_current_user)):
    """List all chat sessions for the current user (grouped by document)."""
    sessions = await ChatSessionService.get_user_sessions(current_user['uid'])
    return {"sessions": sessions, "total": len(sessions)}

