from Database.database import get_db
from datetime import datetime

class ActivityService:
    @staticmethod
    async def log_activity(user_id: str, action_type: str, title: str, details: str = None):
        db = await get_db()
        
        activity = {
            "user_id": user_id,
            "action_type": action_type,
            "title": title,
            "details": details,
            "created_at": datetime.utcnow()
        }
        
        await db.user_activities.insert_one(activity)

    @staticmethod
    async def get_recent_activity(user_id: str, limit: int = 5):
        db = await get_db()
        cursor = db.user_activities.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        activities = await cursor.to_list(length=limit)
        
        for activity in activities:
            activity["id"] = str(activity["_id"])
            del activity["_id"]
            
        return activities
