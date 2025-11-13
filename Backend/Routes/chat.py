from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from Services.gemini_client import ask_question_about_text
from Services import simple_rag_service as rag_service

router = APIRouter()

_stored_text = ""

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = []
    top_k: int = 4

@router.post("/chat")
def chat_with_document(req: ChatRequest):
    """
    RAG-powered chat: retrieves relevant context from vector store and answers questions.
    Also handles general conversation when no relevant context is found.
    """
    question = (req.question or "").strip()
    history = req.history or []

    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    try:
        # Check if this is a general greeting/acknowledgment
        general_responses = {
            "ok": "Feel free to ask me anything about the content!",
            "okay": "What else would you like to know?",
            "thanks": "You're welcome! Ask me anything else.",
            "thank you": "Happy to help! Any other questions?",
            "got it": "Great! What else can I help you with?",
            "alright": "Is there anything else you'd like to know?",
            "sure": "Go ahead, I'm here to help!",
            "yes": "What would you like to know?",
            "no": "Okay! Let me know if you need anything."
        }
        
        question_lower = question.lower()
        
        # Check for exact matches first
        if question_lower in general_responses:
            return {
                "answer": general_responses[question_lower],
                "sources_used": 0
            }
        
        # Use RAG to retrieve relevant context chunks
        context_chunks = rag_service.retrieve_context(question, k=req.top_k)
        
        if not context_chunks:
            # No relevant content found - inform user politely
            return {
                "answer": "I don't have information about that in the loaded content. Please ask questions related to the document you extracted, or extract new content from the Home page.",
                "sources_used": 0
            }
        
        # Combine chunks into context
        context = "\n\n".join(context_chunks)
        
        # Build conversation history for context
        history_text = ""
        if history:
            recent_history = history[-4:]  # Last 4 exchanges
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
        
        # Get AI answer with context
        answer = ask_question_about_text(question, context, history=history)
        
        return {
            "answer": answer,
            "sources_used": len(context_chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
