# Backend/Routes/index_text.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Services import rag_service

router = APIRouter()

class IndexRequest(BaseModel):
    text: str
    source: str = "uploaded"

@router.post("/index")
def index_text(req: IndexRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    count = rag_service.add_text_to_store(text, source=req.source)
    return {"indexed_chunks": count}
