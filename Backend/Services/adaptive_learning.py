# Backend/Services/adaptive_learning.py
"""
Adaptive Learning Path using ML-based recommendations
Analyzes user performance and suggests next topics
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Storage for user learning data
LEARNING_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "learning_progress.json")

def _ensure_data_dir():
    os.makedirs(os.path.dirname(LEARNING_DATA_FILE), exist_ok=True)

def _load_learning_data():
    """Load learning progress data"""
    _ensure_data_dir()
    if os.path.exists(LEARNING_DATA_FILE):
        with open(LEARNING_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}, "topics": {}}

def _save_learning_data(data):
    """Save learning progress data"""
    _ensure_data_dir()
    with open(LEARNING_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

class AdaptiveLearningEngine:
    """ML-based adaptive learning recommendations"""
    
    def __init__(self):
        self.data = _load_learning_data()
    
    def record_concept_study(self, user_id: str, concept: str, time_spent: int = 0):
        """Record that user studied a concept"""
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "concepts_studied": [],
                "quiz_scores": {},
                "total_time": 0,
                "level": 1
            }
        
        user = self.data["users"][user_id]
        if concept not in user["concepts_studied"]:
            user["concepts_studied"].append(concept)
        user["total_time"] += time_spent
        
        _save_learning_data(self.data)
    
    def record_quiz_score(self, user_id: str, topic: str, score: float, difficulty: str = "medium"):
        """Record quiz performance"""
        if user_id not in self.data["users"]:
            self.record_concept_study(user_id, topic)
        
        user = self.data["users"][user_id]
        
        if topic not in user["quiz_scores"]:
            user["quiz_scores"][topic] = []
        
        user["quiz_scores"][topic].append({
            "score": score,
            "difficulty": difficulty,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update user level based on performance
        avg_score = self._calculate_average_score(user_id)
        user["level"] = self._calculate_level(avg_score, len(user["concepts_studied"]))
        
        _save_learning_data(self.data)
    
    def recommend_next_topics(self, user_id: str, available_concepts: List[str], top_k: int = 3) -> List[Dict]:
        """
        Recommend next topics based on:
        1. Topics not yet studied
        2. Similarity to topics user performed well on
        3. Appropriate difficulty level
        """
        if user_id not in self.data["users"]:
            # New user - recommend diverse topics
            return [{"concept": c, "reason": "Beginner topic", "confidence": 0.5} 
                    for c in available_concepts[:top_k]]
        
        user = self.data["users"][user_id]
        studied = set(user["concepts_studied"])
        unstudied = [c for c in available_concepts if c not in studied]
        
        if not unstudied:
            # All topics studied - recommend based on weak areas
            return self._recommend_for_review(user_id, available_concepts, top_k)
        
        # Get topics user performed well on
        strong_topics = self._get_strong_topics(user_id)
        
        if not strong_topics:
            # No quiz data yet - recommend first topics
            return [{"concept": c, "reason": "Foundational topic", "confidence": 0.6} 
                    for c in unstudied[:top_k]]
        
        # Use cosine similarity to find related topics
        recommendations = []
        
        # Simple keyword similarity
        for concept in unstudied:
            similarity = self._calculate_topic_similarity(concept, strong_topics)
            difficulty_match = self._matches_user_level(user["level"], concept)
            
            score = similarity * 0.7 + difficulty_match * 0.3
            
            reason = self._generate_recommendation_reason(similarity, difficulty_match, user["level"])
            
            recommendations.append({
                "concept": concept,
                "reason": reason,
                "confidence": round(score, 2),
                "estimated_difficulty": self._estimate_difficulty(concept)
            })
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations[:top_k]
    
    def get_learning_stats(self, user_id: str) -> Dict:
        """Get comprehensive learning statistics"""
        if user_id not in self.data["users"]:
            return {
                "concepts_studied": 0,
                "quizzes_taken": 0,
                "average_score": 0,
                "level": 1,
                "total_time_minutes": 0,
                "strong_areas": [],
                "weak_areas": [],
                "learning_velocity": "New learner"
            }
        
        user = self.data["users"][user_id]
        avg_score = self._calculate_average_score(user_id)
        
        return {
            "concepts_studied": len(user["concepts_studied"]),
            "quizzes_taken": sum(len(scores) for scores in user["quiz_scores"].values()),
            "average_score": round(avg_score, 1),
            "level": user["level"],
            "total_time_minutes": user["total_time"],
            "strong_areas": self._get_strong_topics(user_id),
            "weak_areas": self._get_weak_topics(user_id),
            "learning_velocity": self._calculate_learning_velocity(user_id)
        }
    
    def predict_quiz_performance(self, user_id: str, topic: str) -> Dict:
        """Predict likely quiz performance for a topic"""
        if user_id not in self.data["users"]:
            return {
                "predicted_score": 50,
                "confidence": "low",
                "recommendation": "Take a practice quiz to establish baseline"
            }
        
        user = self.data["users"][user_id]
        
        # If user has taken quiz on this topic before
        if topic in user["quiz_scores"]:
            scores = [s["score"] for s in user["quiz_scores"][topic]]
            trend = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
            
            return {
                "predicted_score": round(np.mean(scores), 1),
                "confidence": "high",
                "trend": trend,
                "recommendation": "Ready for next difficulty level" if np.mean(scores) > 80 else "More practice recommended"
            }
        
        # Predict based on similar topics
        avg_score = self._calculate_average_score(user_id)
        
        return {
            "predicted_score": round(avg_score, 1),
            "confidence": "medium",
            "recommendation": "New topic - predicted based on overall performance"
        }
    
    # Helper methods
    def _calculate_average_score(self, user_id: str) -> float:
        """Calculate user's average quiz score"""
        user = self.data["users"].get(user_id, {})
        all_scores = []
        for scores in user.get("quiz_scores", {}).values():
            all_scores.extend([s["score"] for s in scores])
        return np.mean(all_scores) if all_scores else 0
    
    def _calculate_level(self, avg_score: float, concepts_count: int) -> int:
        """Calculate user level based on performance"""
        # Level = (average_score / 20) + (concepts / 5)
        score_level = avg_score / 20
        concept_level = concepts_count / 5
        return max(1, min(10, int(score_level + concept_level)))
    
    def _get_strong_topics(self, user_id: str) -> List[str]:
        """Get topics user performed well on (>75% average)"""
        user = self.data["users"].get(user_id, {})
        strong = []
        for topic, scores in user.get("quiz_scores", {}).items():
            avg = np.mean([s["score"] for s in scores])
            if avg > 75:
                strong.append(topic)
        return strong
    
    def _get_weak_topics(self, user_id: str) -> List[str]:
        """Get topics user needs to review (<60% average)"""
        user = self.data["users"].get(user_id, {})
        weak = []
        for topic, scores in user.get("quiz_scores", {}).items():
            avg = np.mean([s["score"] for s in scores])
            if avg < 60:
                weak.append(topic)
        return weak
    
    def _calculate_topic_similarity(self, topic1: str, topic_list: List[str]) -> float:
        """Calculate similarity between topic and list of topics"""
        if not topic_list:
            return 0.0
        
        # Simple keyword overlap
        words1 = set(topic1.lower().split())
        max_similarity = 0
        
        for topic2 in topic_list:
            words2 = set(topic2.lower().split())
            overlap = len(words1.intersection(words2))
            similarity = overlap / max(len(words1), len(words2))
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _matches_user_level(self, user_level: int, concept: str) -> float:
        """Check if concept difficulty matches user level"""
        # Simple heuristic based on concept complexity
        concept_difficulty = self._estimate_difficulty(concept)
        
        if abs(user_level - concept_difficulty) <= 1:
            return 1.0
        elif abs(user_level - concept_difficulty) <= 2:
            return 0.7
        else:
            return 0.4
    
    def _estimate_difficulty(self, concept: str) -> int:
        """Estimate concept difficulty (1-10)"""
        # Simple heuristics
        concept_lower = concept.lower()
        
        beginner_keywords = ['basic', 'introduction', 'fundamentals', 'getting started', 'overview']
        advanced_keywords = ['advanced', 'expert', 'optimization', 'architecture', 'deep']
        
        for keyword in advanced_keywords:
            if keyword in concept_lower:
                return 8
        
        for keyword in beginner_keywords:
            if keyword in concept_lower:
                return 2
        
        # Default to medium difficulty
        return 5
    
    def _generate_recommendation_reason(self, similarity: float, difficulty_match: float, user_level: int) -> str:
        """Generate human-readable reason for recommendation"""
        if similarity > 0.7 and difficulty_match > 0.8:
            return f"Perfect match for your level ({user_level}) and builds on your strengths"
        elif similarity > 0.5:
            return "Related to topics you've mastered"
        elif difficulty_match > 0.8:
            return f"Matches your current skill level (Level {user_level})"
        else:
            return "Expanding your knowledge to new areas"
    
    def _calculate_learning_velocity(self, user_id: str) -> str:
        """Determine learning pace"""
        user = self.data["users"].get(user_id, {})
        concepts_count = len(user.get("concepts_studied", []))
        avg_score = self._calculate_average_score(user_id)
        
        if concepts_count > 20 and avg_score > 80:
            return "Fast - Mastering concepts quickly"
        elif concepts_count > 10 and avg_score > 70:
            return "Steady - Consistent progress"
        elif concepts_count < 5:
            return "Getting started"
        else:
            return "Moderate - Take your time to master fundamentals"
    
    def _recommend_for_review(self, user_id: str, available_concepts: List[str], top_k: int) -> List[Dict]:
        """Recommend topics for review"""
        weak_topics = self._get_weak_topics(user_id)
        
        recommendations = []
        for topic in weak_topics[:top_k]:
            if topic in available_concepts:
                recommendations.append({
                    "concept": topic,
                    "reason": "Review recommended - previous performance below 60%",
                    "confidence": 0.9,
                    "type": "review"
                })
        
        return recommendations

# Global instance
_learning_engine = AdaptiveLearningEngine()

def get_learning_engine() -> AdaptiveLearningEngine:
    """Get global learning engine instance"""
    return _learning_engine
