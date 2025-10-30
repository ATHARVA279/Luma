# Backend/Routes/rag_chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from Services import rag_service
from Services.gemini_client import ask_question_about_text  # adjust import path to your project

router = APIRouter()

class RAGRequest(BaseModel):
    question: str
    top_k: int = 4
    # optional: if user uploaded new text with question use it to index
    context_text: Optional[str] = None
    source: Optional[str] = "user_uploaded"
    history: Optional[list] = None

@router.post("/rag_chat")
def rag_chat(req: RAGRequest):
    q = (req.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question required")

    # optionally index the provided context_text (use carefully; best to index on separate endpoint)
    if req.context_text:
        rag_service.add_text_to_store(req.context_text, source=req.source or "uploaded")

    # retrieve top-k context passages
    context_chunks = rag_service.retrieve_context(q, k=req.top_k)
    # join them into a single context string (with separators)
    if context_chunks:
        context = "\n\n---\n\n".join(context_chunks)
    else:
        context = ""  # empty -> ask model to say if no info found

    # build a clear prompt for the model — we keep this small and rely on gemini to answer
    prompt = f"""You are an expert tutor. Use the following context (from the user's materials) to answer the question. 
If the answer is not present in the provided context, say 'Not found in the provided material.' Be concise, and give a short explanation and one example if applicable.

Context:
{context}

Question: {q}
    """

    # pass to your existing gemini helper (which expects question and full context). 
    # If your helper signature differs, adapt accordingly.
    try:
        answer = ask_question_about_text(q, context, history=req.history or [])
        return {"answer": answer, "context_used_count": len(context_chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
