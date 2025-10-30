from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from Services.gemini_client import generate_mcq_from_text
from Services import simple_rag_service as rag_service

router = APIRouter()

# Temporary storage for extracted text (backward compatibility)
_stored_text = ""

class QuizRequest(BaseModel):
    count: int = 10
    topics: List[str] = []

@router.post("/quiz/generate")
def generate_quiz_with_topics(request: QuizRequest):
    """
    Generate quiz questions based on selected topics using RAG context.
    """
    try:
        count = max(5, min(20, request.count))
        topics = request.topics
        
        if not topics:
            raise HTTPException(status_code=400, detail="Please select at least one topic")
        
        # Retrieve relevant context for each topic
        all_context = []
        for topic in topics:
            chunks = rag_service.retrieve_context(topic, k=10)
            if chunks:
                all_context.extend(chunks)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_context = []
        for chunk in all_context:
            if chunk not in seen:
                seen.add(chunk)
                unique_context.append(chunk)
        
        if not unique_context:
            raise HTTPException(
                status_code=400, 
                detail="No content found for selected topics. Please extract content first."
            )
        
        # Combine context
        combined_text = "\n\n".join(unique_context)
        
        # Generate quiz with improved prompt
        quiz_json = generate_mcq_from_text(
            combined_text, 
            count=count, 
            topics=topics
        )
        
        return {
            "questions": quiz_json, 
            "topics_covered": topics,
            "context_chunks_used": len(unique_context)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@router.get("/quiz")
def generate_quiz(count: int = 10):
    """
    Generate quiz questions using RAG context from vector store.
    Retrieves all available chunks for quiz generation.
    """
    try:
        # Get all available chunks (use empty query with high k to get everything)
        all_chunks = rag_service.retrieve_context("", k=100)
        
        # Also try with a generic query if empty query doesn't work
        if not all_chunks:
            all_chunks = rag_service.retrieve_context("content information", k=100)
        
        if not all_chunks:
            raise HTTPException(status_code=400, detail="No content available. Please extract text first from Home page.")
        
        # Combine all available chunks
        combined_text = "\n\n".join(all_chunks)
        
        # Validate we have sufficient content
        if len(combined_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Insufficient content for quiz generation.")
        
        # Generate quiz from this context
        count = max(5, min(15, count))
        quiz_json = generate_mcq_from_text(combined_text, count=count)
        
        return {"questions": quiz_json, "context_chunks_used": len(all_chunks), "content_length": len(combined_text)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
