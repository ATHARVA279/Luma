from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Services.text_cleaner import extract_text_from_url
from Services import simple_rag_service as simple_rag
from Services import advanced_rag_service as advanced_rag
from Services.gemini_client import extract_concepts_from_text
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

# Import the shared storage for backward compatibility
import Routes.quiz as quiz_module
import Routes.chat as chat_module

class ExtractRequest(BaseModel):
    url: str
    use_advanced_rag: bool = True

@router.delete("/clear-store")
async def clear_vector_store():
    """
    Clear all content from vector stores (both simple and advanced RAG).
    """
    try:
        simple_rag.clear_store()
        advanced_rag.clear_store()
        quiz_module._stored_text = ""
        chat_module._stored_text = ""
        return {"message": "All vector stores cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear stores: {str(e)}")

@router.post("/extract")
async def extract_from_url(req: ExtractRequest):
    """
    Extract cleaned textual content from a web URL and index it into vector store.
    Uses both simple and advanced RAG for maximum compatibility.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        # Extract text from URL
        text = extract_text_from_url(url)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text found at the provided URL")
        
        # Clear existing stores first to avoid mixing content
        try:
            simple_rag.clear_store()
            advanced_rag.clear_store()
        except Exception as e:
            print(f"⚠️ Store clearing warning: {str(e)}")
        
        # Store text for backward compatibility
        quiz_module._stored_text = text
        chat_module._stored_text = text
        
        # Index into BOTH simple and advanced RAG stores
        simple_chunks = 0
        advanced_chunks = 0
        
        try:
            # Index into simple RAG (for compatibility)
            simple_chunks = simple_rag.add_text_to_store(text, url)
        except Exception as e:
            print(f"⚠️ Simple RAG indexing error: {str(e)}")
        
        try:
            # Index into advanced RAG with metadata
            metadata = {"url": url, "indexed_at": str(asyncio.get_event_loop().time())}
            advanced_chunks = advanced_rag.add_text_to_store(text, url, metadata)
        except Exception as e:
            print(f"⚠️ Advanced RAG indexing error: {str(e)}")
        
        chunks_indexed = max(simple_chunks, advanced_chunks)
        
        # Try to extract concepts (optional - don't fail if this doesn't work)
        concepts_list = []
        try:
            # Use a truncated version of text for faster concept extraction
            concept_text = text[:5000] if len(text) > 5000 else text
            concepts_data = extract_concepts_from_text(concept_text)
            concepts_list = concepts_data.get("concepts", []) if concepts_data else []
        except Exception as e:
            print(f"⚠️ Concept extraction error (continuing anyway): {str(e)}")
            # Use simple fallback - extract common nouns/phrases as concepts
            import re
            # Extract capitalized words and common technical terms
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text[:2000])
            # Get unique words and limit to 10
            unique_words = list(dict.fromkeys(words))[:10]
            concepts_list = unique_words if unique_words else ["Content Overview", "Key Topics", "Main Concepts"]
        
        return {
            "url": url,
            "text": text[:500] + "..." if len(text) > 500 else text,
            "full_length": len(text),
            "chunks_indexed": chunks_indexed,
            "concepts": concepts_list,
            "relationships": [],
            "rag_methods": {
                "simple": simple_chunks > 0,
                "advanced": advanced_chunks > 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fatal error in extract: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    """
    Extract cleaned textual content from a web URL.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        text = extract_text_from_url(url)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text found at the provided URL")
        # For safety, slice very long text on the response side if needed (frontend can request chunks)
        return {"url": url, "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
