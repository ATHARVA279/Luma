import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

_jobs: Dict[str, Dict[str, Any]] = {}

class JobService:
    @staticmethod
    def create_job(job_type: str, user_id: str, metadata: Dict = None) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        job = {
            "id": job_id,
            "type": job_type,
            "user_id": user_id,
            "status": "pending",
            "progress": 0,
            "result": None,
            "error": None,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now
        }
        
        _jobs[job_id] = job
        return job_id

    @staticmethod
    def update_job(job_id: str, status: str = None, progress: int = None, result: Dict = None, error: str = None):
        if job_id not in _jobs:
            return
            
        job = _jobs[job_id]
        now = datetime.utcnow().isoformat()
        
        if status:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error
            
        job["updated_at"] = now

    @staticmethod
    def get_job(job_id: str, user_id: str) -> Optional[Dict]:
        if job_id not in _jobs:
            return None
            
        job = _jobs[job_id]
        if job["user_id"] != user_id:
            return None
            
        return job

    @staticmethod
    def list_user_jobs(user_id: str, job_type: str = None) -> List[Dict]:
        user_jobs = [
            job for job in _jobs.values() 
            if job["user_id"] == user_id and (job_type is None or job["type"] == job_type)
        ]
        
        user_jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return user_jobs

    @staticmethod
    def cleanup_old_jobs(hours: int = 24):
        pass
