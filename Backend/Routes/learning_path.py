# Backend/Routes/learning_path.py
"""
Adaptive Learning Path routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from Services.adaptive_learning import get_learning_engine

router = APIRouter()

class StudyRecordRequest(BaseModel):
    user_id: str
    concept: str
    time_spent: Optional[int] = 0

class QuizScoreRequest(BaseModel):
    user_id: str
    topic: str
    score: float
    difficulty: Optional[str] = "medium"

class RecommendationRequest(BaseModel):
    user_id: str
    available_concepts: List[str]
    top_k: Optional[int] = 3

@router.post("/learning/record-study")
def record_study_session(req: StudyRecordRequest):
    """Record that a user studied a concept"""
    engine = get_learning_engine()
    engine.record_concept_study(req.user_id, req.concept, req.time_spent)
    
    return {
        "message": "Study session recorded",
        "user_id": req.user_id,
        "concept": req.concept
    }

@router.post("/learning/record-quiz")
def record_quiz_performance(req: QuizScoreRequest):
    """Record quiz performance"""
    engine = get_learning_engine()
    engine.record_quiz_score(req.user_id, req.topic, req.score, req.difficulty)
    
    # Get updated stats
    stats = engine.get_learning_stats(req.user_id)
    
    return {
        "message": "Quiz score recorded",
        "user_id": req.user_id,
        "new_level": stats["level"],
        "average_score": stats["average_score"]
    }

@router.post("/learning/recommendations")
def get_recommendations(req: RecommendationRequest):
    """Get personalized topic recommendations"""
    engine = get_learning_engine()
    recommendations = engine.recommend_next_topics(
        req.user_id,
        req.available_concepts,
        req.top_k
    )
    
    return {
        "user_id": req.user_id,
        "recommendations": recommendations,
        "total": len(recommendations)
    }

@router.get("/learning/stats/{user_id}")
def get_user_stats(user_id: str):
    """Get comprehensive learning statistics"""
    engine = get_learning_engine()
    stats = engine.get_learning_stats(user_id)
    
    return {
        "user_id": user_id,
        "stats": stats
    }

@router.get("/learning/predict/{user_id}/{topic}")
def predict_performance(user_id: str, topic: str):
    """Predict quiz performance for a topic"""
    engine = get_learning_engine()
    prediction = engine.predict_quiz_performance(user_id, topic)
    
    return {
        "user_id": user_id,
        "topic": topic,
        "prediction": prediction
    }
