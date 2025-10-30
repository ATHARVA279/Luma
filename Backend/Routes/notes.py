# Backend/Routes/notes.py
"""
Automated Note Generation routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from Services.note_generator import (
    generate_study_notes,
    generate_quick_summary,
    extract_key_concepts
)
from Services import advanced_rag_service as advanced_rag
from Services import simple_rag_service as simple_rag

router = APIRouter()

class NotesRequest(BaseModel):
    topic: str
    content: Optional[str] = None
    use_stored_content: bool = True

class SummaryRequest(BaseModel):
    content: str
    max_sentences: Optional[int] = 3

@router.post("/notes/generate")
def generate_notes(req: NotesRequest):
    """
    Generate comprehensive study notes from content
    Includes: summary, key points, definitions, flashcards, mind map
    """
    
    try:
        # Get content from stored RAG or provided content
        if req.use_stored_content and not req.content:
            # Try advanced RAG first (hybrid search)
            results = advanced_rag.hybrid_search(req.topic, k=10)
            
            # Fallback to simple RAG if advanced returns nothing
            if not results:
                context_chunks = simple_rag.retrieve_context(req.topic, k=10)
                if context_chunks:
                    content = "\n\n".join(context_chunks)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No content found. Please extract content first or provide content directly."
                    )
            else:
                content = "\n\n".join([r["content"] for r in results])
        elif req.content:
            content = req.content
        else:
            raise HTTPException(status_code=400, detail="No content available")
        
        # Generate comprehensive notes
        notes = generate_study_notes(content, req.topic)
        
        return {
            "success": True,
            "topic": req.topic,
            "notes": notes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Note generation failed: {str(e)}")

@router.post("/notes/summary")
def create_summary(req: SummaryRequest):
    """Generate quick summary of content"""
    
    if not req.content or len(req.content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content too short for summarization")
    
    try:
        summary = generate_quick_summary(req.content, req.max_sentences)
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(req.content),
            "compression_ratio": round(len(summary) / len(req.content), 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.post("/notes/concepts")
def get_key_concepts(content: str, top_n: int = 10):
    """Extract key concepts from content"""
    
    if not content or len(content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content too short")
    
    try:
        concepts = extract_key_concepts(content, top_n)
        
        return {
            "success": True,
            "concepts": concepts,
            "count": len(concepts)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept extraction failed: {str(e)}")

@router.get("/notes/flashcards/{topic}")
def get_flashcards_for_topic(topic: str, count: int = 10):
    """Get flashcards for a specific topic from stored content"""
    
    try:
        # Get content about topic - try advanced RAG first
        results = advanced_rag.hybrid_search(topic, k=8)
        
        # Fallback to simple RAG
        if not results:
            context_chunks = simple_rag.retrieve_context(topic, k=8)
            if not context_chunks:
                raise HTTPException(status_code=404, detail=f"No content found for topic: {topic}")
            content = "\n\n".join(context_chunks)
        else:
            content = "\n\n".join([r["content"] for r in results])
        
        # Generate full notes (includes flashcards)
        notes = generate_study_notes(content, topic)
        
        return {
            "topic": topic,
            "flashcards": notes["flashcards"][:count],
            "total_available": len(notes["flashcards"])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")

@router.get("/notes/mind-map/{topic}")
def get_mind_map(topic: str):
    """Get mind map structure for a topic"""
    
    try:
        # Get content about topic - try advanced RAG first
        results = advanced_rag.hybrid_search(topic, k=8)
        
        # Fallback to simple RAG
        if not results:
            context_chunks = simple_rag.retrieve_context(topic, k=8)
            if not context_chunks:
                raise HTTPException(status_code=404, detail=f"No content found for topic: {topic}")
            content = "\n\n".join(context_chunks)
        else:
            content = "\n\n".join([r["content"] for r in results])
        
        # Generate notes (includes mind map)
        notes = generate_study_notes(content, topic)
        
        return {
            "topic": topic,
            "mind_map": notes["mind_map"],
            "key_points_count": len(notes["key_points"])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mind map generation failed: {str(e)}")
