from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import asyncio
from Services.gemini_client import extract_concepts_from_text
from Middleware.auth import get_current_user
from config import Config
from models.requests import ExtractRequest
from Services.job_service import JobService
from Services.chunking_service import TextChunker
from Database.database import get_db
from datetime import datetime
from bson import ObjectId
import httpx
from bs4 import BeautifulSoup
import re
import warnings
from bs4 import MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
from Middleware.rate_limit import limit_extract

router = APIRouter()

async def process_extraction_job(job_id: str, url: str, user_id: str):
    try:
        JobService.update_job(job_id, status="processing", progress=10)
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=Config.HTTP_TIMEOUT) as client:
                headers = {
                    'User-Agent': Config.USER_AGENT,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = await client.get(url, headers=headers)
                html = response.text
        except Exception as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
            
        JobService.update_job(job_id, progress=30)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not text.strip():
            raise Exception("No text found at the provided URL")
        
        JobService.update_job(job_id, progress=40)
        
        chunker = TextChunker(chunk_size=Config.DEFAULT_CHUNK_SIZE, overlap=Config.DEFAULT_CHUNK_OVERLAP)
        chunks_data = chunker.chunk_by_sentences(text)
        chunk_texts = [c["text"] for c in chunks_data]
        
        JobService.update_job(job_id, progress=60)
        
        concepts_list = []
        try:
            extraction_result = await asyncio.to_thread(extract_concepts_from_text, text)
            concepts_list = extraction_result.get("concepts", [])
            
            if not concepts_list:
                 concepts_list = ["General Content"]
                 
        except Exception as e:
            print(f"Concept extraction error: {e}")
            concepts_list = ["General Content"]

        JobService.update_job(job_id, progress=70)
        
        db = await get_db()
        
        concepts_structured = []
        if concepts_list:
            for concept in concepts_list:
                concepts_structured.append({
                    "name": concept,
                    "extracted_at": datetime.utcnow()
                })
        
        relationships = extraction_result.get("relationships", [])
        
        document = {
            "user_id": user_id,
            "url": url,
            "title": concepts_list[0] if concepts_list else "Untitled Document",
            "status": "completed",
            "concepts": concepts_structured,
            "relationships": relationships,
            "metadata": {
                "total_chunks": len(chunks_data),
                "total_concepts": len(concepts_list),
                "text_length": len(text),
                "extraction_method": "gemini-2.5-flash"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.documents.insert_one(document)
        doc_id = str(result.inserted_id)
        
        chunk_docs = []
        for c in chunks_data:
            chunk_docs.append({
                "document_id": result.inserted_id,
                "user_id": user_id,
                "chunk_index": c["chunk_index"],
                "text": c["text"],
                "metadata": {
                    "start_sentence": c["start_sentence"],
                    "end_sentence": c["end_sentence"],
                    "type": "sentence_group"
                },
                "created_at": datetime.utcnow().isoformat()
            })
            
        if chunk_docs:
            insert_result = await db.document_chunks.insert_many(chunk_docs)
            chunk_oids = insert_result.inserted_ids
            
            try:
                await db.document_chunks.create_index([("document_id", 1), ("chunk_index", 1)])
            except:
                pass
        
        JobService.update_job(job_id, progress=80)

        from Services.persistent_vector_store import PersistentVectorStore
        
        store = PersistentVectorStore()
        for i, chunk_doc in enumerate(chunk_docs):
            tokens = chunk_doc["text"].lower().split()
            await store.save_bm25_tokens(user_id, doc_id, chunk_oids[i], tokens)
            
        chunks_indexed = len(chunk_docs)
        await db.documents.update_one(
            {"_id": result.inserted_id},
            {"$set": {"summary": f"Extracted {chunks_indexed} chunks. Key topics: {', '.join(concepts_list[:3])}..."}}
        )

        from Services.activity_service import ActivityService
        await ActivityService.log_activity(user_id, "extract", document["title"], f"Extracted {len(chunks_data)} chunks")

        JobService.update_job(job_id, status="completed", progress=100, result={"document_id": doc_id})
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Job failed: {str(e)}")
        print(f"DEBUG: Full traceback:\n{error_trace}")
    
        from Services.credit_service import CreditService
        await CreditService.refund_credits(user_id, "extract")
        
        JobService.update_job(job_id, status="failed", error=f"{str(e)}. Check server logs for details.")

@router.post("/extract", dependencies=[Depends(limit_extract)])
async def extract_url(extract_req: ExtractRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    db = await get_db()
    existing_doc = await db.documents.find_one({
        "user_id": current_user['uid'],
        "url": str(extract_req.url)
    })
    
    if existing_doc:
        return {
            "status": "already_extracted",
            "document_id": str(existing_doc['_id']),
            "message": "This URL has already been extracted",
            "extracted_at": existing_doc.get('created_at'),
            "concepts_count": len(existing_doc.get('concepts', []))
        }
    
    from Services.credit_service import CreditService
    await CreditService.check_and_deduct(current_user['uid'], "extract")

    job_id = JobService.create_job("extraction", current_user['uid'], {"url": str(extract_req.url)})
    
    background_tasks.add_task(process_extraction_job, job_id, str(extract_req.url), current_user['uid'])
    
    return {"job_id": job_id, "status": "pending"}

@router.get("/extract/status/{job_id}")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = JobService.get_job(job_id, current_user['uid'])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/extract/jobs")
async def list_jobs(current_user: dict = Depends(get_current_user)):
    return JobService.list_user_jobs(current_user['uid'], "extraction")

@router.delete("/clear-store")
async def clear_database(current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        await db.documents.delete_many({"user_id": current_user['uid']})
        await db.document_chunks.delete_many({"user_id": current_user['uid']})
        
        return {"message": "Database and vector stores cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

