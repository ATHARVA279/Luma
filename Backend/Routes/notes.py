from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from Services.note_generator import (
    generate_study_notes,
    generate_quick_summary,
    extract_key_concepts
)
from Services.persistent_vector_store import PersistentVectorStore
from Middleware.rate_limit import limit_notes

router = APIRouter()

from models.requests import GenerateNotesRequest as NotesRequest, SummaryRequest

from Middleware.auth import get_current_user
from Database.database import get_db
from fastapi import Depends
from datetime import datetime
from bson import ObjectId

@router.post("/notes/generate", dependencies=[Depends(limit_notes)])
async def generate_notes(req: NotesRequest, current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        
        if not req.document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required for note generation"
            )
        
        try:
            doc_oid = ObjectId(req.document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document_id format")
        
        existing_note = await db.concept_notes.find_one({
            "user_id": current_user['uid'],
            "document_id": doc_oid,
            "concept_name": req.topic
        })
        
        if existing_note:
            return {
                "success": True,
                "topic": req.topic,
                "document_id": req.document_id,
                "notes": existing_note['content'],
                "source": "cache",
                "generated_at": existing_note.get('generated_at')
            }

        from Services.credit_service import CreditService
        transaction_id = await CreditService.check_and_deduct(current_user['uid'], "notes")

        try:
            if req.use_stored_content and not req.content:
                store = PersistentVectorStore()
                results = await store.search_bm25(
                    current_user['uid'], 
                    req.topic, 
                    k=10, 
                    document_id=req.document_id
                )
                
                if not results:
                    raise HTTPException(
                        status_code=400,
                        detail="No content found for this topic in the specified document."
                    )
                
                content = "\\n\\n".join([r["content"] for r in results])
            elif req.content:
                content = req.content
            else:
                raise HTTPException(status_code=400, detail="No content available")
            
            notes = generate_study_notes(content, req.topic)
            
            document = await db.documents.find_one({"_id": doc_oid})
            concept_id = None
            if document and "concepts" in document:
                for concept in document['concepts']:
                    if concept.get('name', '').lower() == req.topic.lower():
                        concept_id = concept.get('_id')
                        break
            
            new_note = {
                "user_id": current_user['uid'],
                "document_id": doc_oid,
                "concept_name": req.topic,
                "concept_id": concept_id,
                
                "content": notes,
                "type": "comprehensive_notes",
                
                "generated_at": datetime.utcnow(),
                "generation_method": "gemini-2.5-flash"
            }
            await db.concept_notes.insert_one(new_note)
            
            from Services.activity_service import ActivityService
            await ActivityService.log_activity(current_user['uid'], "note", req.topic, "Generated study notes")

            await CreditService.complete_transaction(current_user['uid'], transaction_id)
            
            return {
                "success": True,
                "topic": req.topic,
                "document_id": req.document_id,
                "notes": notes,
                "source": "generated"
            }
        except Exception as e:
            await CreditService.refund_by_action(current_user['uid'], "notes", transaction_id)
            raise HTTPException(status_code=500, detail=f"Note generation failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/notes/summary", dependencies=[Depends(limit_notes)])
async def create_summary(req: SummaryRequest, current_user: dict = Depends(get_current_user)):
    if not req.content or len(req.content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content too short for summarization")
    
    try:
        summary = generate_quick_summary(req.content, req.max_sentences)
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(req.content),
            "compression_ratio": round(len(summary) / len(req.content), 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

class ConceptsRequest(BaseModel):
    content: str
    top_n: int = 10

@router.post("/notes/concepts", dependencies=[Depends(limit_notes)])
async def get_key_concepts(req: ConceptsRequest, current_user: dict = Depends(get_current_user)):
    """Extract key concepts from content"""
    
    if not req.content or len(req.content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content too short")
    
    try:
        concepts = extract_key_concepts(req.content, req.top_n)
        
        return {
            "success": True,
            "concepts": concepts,
            "count": len(concepts)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept extraction failed: {str(e)}")

@router.get("/notes/flashcards/{topic}", dependencies=[Depends(limit_notes)])
async def get_flashcards_for_topic(topic: str, count: int = 10, current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        
        existing_note = await db.notes.find_one({
            "user_id": current_user['uid'],
            "topic": topic
        })
        
        if existing_note and "content" in existing_note and "flashcards" in existing_note["content"]:
            flashcards = existing_note["content"]["flashcards"]
            return {
                "topic": topic,
                "flashcards": flashcards[:count],
                "total_available": len(flashcards),
                "source": "cache"
            }

        store = PersistentVectorStore()
        results = await store.search_bm25(current_user['uid'], topic, k=8, document_id=None)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No content found for topic: {topic}")
        
        content = "\n\n".join([r["content"] for r in results])
        
        notes = generate_study_notes(content, topic)
        
        return {
            "topic": topic,
            "flashcards": notes["flashcards"][:count],
            "total_available": len(notes["flashcards"]),
            "source": "generated"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")

@router.get("/notes/mind-map/{topic}", dependencies=[Depends(limit_notes)])
async def get_mind_map(topic: str, current_user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        
        existing_note = await db.notes.find_one({
            "user_id": current_user['uid'],
            "topic": topic
        })
        
        if existing_note and "content" in existing_note and "mind_map" in existing_note["content"]:
            return {
                "topic": topic,
                "mind_map": existing_note["content"]["mind_map"],
                "key_points_count": len(existing_note["content"].get("key_points", [])),
                "source": "cache"
            }

        store = PersistentVectorStore()
        results = await store.search_bm25(current_user['uid'], topic, k=8, document_id=None)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No content found for topic: {topic}")
        
        content = "\n\n".join([r["content"] for r in results])
        
        notes = generate_study_notes(content, topic)
        
        return {
            "topic": topic,
            "mind_map": notes["mind_map"],
            "key_points_count": len(notes["key_points"]),
            "source": "generated"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mind map generation failed: {str(e)}")
