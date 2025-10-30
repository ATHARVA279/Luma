from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Services import simple_rag_service as rag_service
from Services.gemini_client import ask_question_about_text

router = APIRouter()

class ConceptDetailRequest(BaseModel):
    concept: str
    top_k: int = 5

@router.post("/concept-detail")
def get_concept_detail(req: ConceptDetailRequest):
    """
    Get detailed explanation of a concept using RAG (retrieves relevant context from vector store).
    """
    concept = req.concept.strip()
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    
    try:
        # Use RAG to retrieve relevant context about this concept
        context_chunks = rag_service.retrieve_context(concept, k=req.top_k)
        
        if not context_chunks:
            raise HTTPException(status_code=404, detail="No information found about this concept")
        
        context = "\n\n".join(context_chunks)
        
        # Ask AI to explain the concept using the retrieved context
        question = f"Explain the concept '{concept}' in detail with examples."
        explanation = ask_question_about_text(question, context, history=[])
        
        return {
            "concept": concept,
            "explanation": explanation,
            "sources_used": len(context_chunks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get concept detail: {str(e)}")
