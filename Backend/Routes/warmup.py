from fastapi import APIRouter
from Services import simple_rag_service as simple_rag
from Services import advanced_rag_service as advanced_rag

router = APIRouter()

@router.get("/warmup")
def warmup_ml_models():
    """
    Warmup endpoint to initialize both RAG services and check system status.
    """
    try:
        # Get store info from both RAG systems
        simple_info = simple_rag.get_store_info()
        advanced_info = advanced_rag.get_store_info()
        
        return {
            "status": "ready",
            "message": "Luma - All systems operational",
            "features": {
                "rag": {
                    "simple": "TF-IDF (backward compatible)",
                    "advanced": "Hybrid Search (TF-IDF + BM25 + RRF)",
                    "simple_store": simple_info,
                    "advanced_store": advanced_info
                },
                "chat": {
                    "basic": "Simple Q&A with RAG",
                    "advanced": "Conversational memory + context-aware search"
                },
                "learning": {
                    "adaptive_path": "ML-based recommendations",
                    "progress_tracking": "User performance analytics",
                    "spaced_repetition": "Optimized review scheduling"
                },
                "notes": {
                    "generation": "AI-powered study notes",
                    "flashcards": "Automatic flashcard creation",
                    "mind_maps": "Visual knowledge structures"
                }
            },
            "ml_models": [
                "Google Gemini 2.0 Flash (LLM)",
                "scikit-learn TF-IDF (keyword search)",
                "BM25 (probabilistic ranking)",
                "Cosine Similarity (semantic matching)"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"System initialization failed: {str(e)}"
        }
