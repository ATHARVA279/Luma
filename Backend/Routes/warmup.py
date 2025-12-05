from fastapi import APIRouter, Request
from config import Config

router = APIRouter()

@router.get("/rate-limit/status")
def get_rate_limit_status(request: Request):
    return {
        "quotas": {
            "quiz": Config.RATE_LIMIT_QUIZ,
            "notes": Config.RATE_LIMIT_NOTES,
            "chat": Config.RATE_LIMIT_CHAT,
            "extraction": Config.RATE_LIMIT_EXTRACT
        },
        "reset_period": "Per minute/hour based on endpoint",
        "message": "Limits are applied per user."
    }

@router.get("/warmup")
async def warmup_system():
    try:
        from Database.database import get_db
        db = await get_db()
        
        doc_count = await db.documents.count_documents({})
        
        return {
            "status": "ready",
            "message": "Luma - All systems operational",
            "database": {
                "status": "connected",
                "documents": doc_count
            },
            "features": {
                "rag": {
                    "storage": "MongoDB-backed BM25 search",
                    "search": "Persistent vector store with user-scoped data"
                },
                "chat": {
                    "basic": "Simple Q&A with RAG",
                    "advanced": "Conversational memory + context-aware search"
                },
                "learning": {
                    "extraction": "URL content extraction with chunking",
                    "quiz_generation": "AI-powered quiz creation",
                    "note_generation": "Automated study notes"
                },
                "notes": {
                    "generation": "AI-powered study notes",
                    "flashcards": "Automatic flashcard creation",
                    "mind_maps": "Visual knowledge structures",
                    "caching": "MongoDB-based persistence"
                }
            },
            "ml_models": [
                f"Google Gemini {Config.GEMINI_MODEL} (LLM)",
                "BM25 (probabilistic ranking)",
                "MongoDB Atlas Search (vector storage)"
            ],
            "configuration": {
                "chunk_size": Config.DEFAULT_CHUNK_SIZE,
                "chunk_overlap": Config.DEFAULT_CHUNK_OVERLAP,
                "quiz_range": f"{Config.MIN_QUIZ_QUESTIONS}-{Config.MAX_QUIZ_QUESTIONS} questions"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"System initialization failed: {str(e)}",
            "details": "Check database connection and environment variables"
        }
