from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List
from Services.gemini_client import generate_mcq_from_text
from Middleware.rate_limit import limit_quiz
from config import Config


router = APIRouter()

from models.requests import GenerateQuizRequest as QuizRequest

from Middleware.auth import get_current_user
from Database.database import get_db
from datetime import datetime

class QuizResultRequest(BaseModel):
    score: int
    total: int
    topics: List[str]
    document_id: str = None

@router.post("/quiz/result")
async def save_quiz_result(result: QuizResultRequest, current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        
        quiz_result = {
            "user_id": current_user['uid'],
            "score": result.score,
            "total": result.total,
            "percentage": (result.score / result.total) * 100 if result.total > 0 else 0,
            "topics": result.topics,
            "document_id": result.document_id,
            "created_at": datetime.utcnow()
        }
        
        await db.quiz_results.insert_one(quiz_result)
        
        from Services.activity_service import ActivityService
        await ActivityService.log_activity(
            current_user['uid'], 
            "quiz_result", 
            f"Scored {result.score}/{result.total}", 
            f"Topics: {', '.join(result.topics[:2])}"
        )
        
        return {"message": "Result saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save result: {str(e)}")

@router.post("/quiz/generate", dependencies=[Depends(limit_quiz)])
async def generate_quiz_with_topics(quiz_req: QuizRequest, current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        
        if not quiz_req.document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required for quiz generation"
            )
        
        from bson import ObjectId
        try:
            doc_oid = ObjectId(quiz_req.document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document_id format")
        
        topic_key = ",".join(sorted(quiz_req.topics))
        
        existing_quiz = await db.document_quizzes.find_one({
            "user_id": current_user['uid'],
            "document_id": doc_oid,
            "topic_key": topic_key,
            "count": quiz_req.count
        })
        
        if existing_quiz:
            return {
                "questions": existing_quiz['questions'],
                "topics_covered": existing_quiz['topics_covered'],
                "document_id": quiz_req.document_id,
                "context_chunks_used": existing_quiz.get('context_chunks_used', 0),
                "source": "cache",
                "generated_at": existing_quiz.get('generated_at')
            }

        from Services.credit_service import CreditService
        transaction_id = await CreditService.check_and_deduct(current_user['uid'], "quiz")

        try:
            count = max(Config.MIN_QUIZ_QUESTIONS, min(Config.MAX_QUIZ_QUESTIONS, quiz_req.count))
            topics = quiz_req.topics
            
            if not topics:
                raise HTTPException(status_code=400, detail="Please select at least one topic")
        
            from Services.persistent_vector_store import PersistentVectorStore
            store = PersistentVectorStore()
            
            all_context = []
            for topic in topics:
                results = await store.search_bm25(
                    current_user['uid'], 
                    topic, 
                    k=10, 
                    document_id=quiz_req.document_id
                )
                if results:
                    all_context.extend([r["content"] for r in results])
            
            seen = set()
            unique_context = []
            for chunk in all_context:
                if chunk not in seen:
                    seen.add(chunk)
                    unique_context.append(chunk)
            
            if not unique_context:
                raise HTTPException(
                    status_code=400, 
                    detail="No content found for these topics in the specified document."
                )
            
            combined_text = "\\n\\n".join(unique_context)
            
            quiz_json = generate_mcq_from_text(
                combined_text, 
                count=count, 
                topics=topics
            )
            
            new_quiz = {
                "user_id": current_user['uid'],
                "document_id": doc_oid,
                "topic_key": topic_key,
                "topics_covered": topics,
                "questions": quiz_json,
                "count": count,
                "context_chunks_used": len(unique_context),
                "generated_at": datetime.utcnow(),
                "generation_method": "gemini-2.5-flash"
            }
            await db.document_quizzes.insert_one(new_quiz)
            
            from Services.activity_service import ActivityService
            await ActivityService.log_activity(current_user['uid'], "quiz", f"Quiz: {', '.join(topics[:2])}", f"Generated {count} questions")

            await CreditService.complete_transaction(current_user['uid'], transaction_id)
            
            return {
                "questions": quiz_json, 
                "topics_covered": topics,
                "document_id": quiz_req.document_id,
                "context_chunks_used": len(unique_context),
                "source": "generated"
            }
        except Exception as e:
            await CreditService.refund_by_action(current_user['uid'], "quiz", transaction_id)
            raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/quiz", dependencies=[Depends(limit_quiz)])
async def generate_quiz(count: int = 10, current_user: dict = Depends(get_current_user)):
    try:
        from Services.persistent_vector_store import PersistentVectorStore
        store = PersistentVectorStore()
        
        all_results = await store.search_bm25(current_user['uid'], "", k=100, document_id=None)
        
        if not all_results:
            all_results = await store.search_bm25(current_user['uid'], "content information", k=100, document_id=None)
        
        if not all_results:
            raise HTTPException(status_code=400, detail="No content available. Please extract text first from Home page.")
        
        all_chunks = [r["content"] for r in all_results]
        
        combined_text = "\n\n".join(all_chunks)
        
        if len(combined_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Insufficient content for quiz generation.")
        
        count = max(Config.MIN_QUIZ_QUESTIONS, min(Config.MAX_QUIZ_QUESTIONS, count))
        quiz_json = generate_mcq_from_text(combined_text, count=count)
        
        return {"questions": quiz_json, "context_chunks_used": len(all_chunks), "content_length": len(combined_text)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@router.delete("/quiz/cache")
async def clear_quiz_cache(current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        result = await db.quizzes.delete_many({"user_id": current_user['uid']})
        return {
            "message": "Quiz cache cleared successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
