from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Services.gemini_client import extract_concepts_from_text

router = APIRouter()

# Temporary storage for extracted text (in production, use a database)
_stored_text = ""

class ConceptsRequest(BaseModel):
    text: str

@router.get("/concepts")
def generate_concepts():
    """
    Uses Gemini to extract concepts and relationships from the stored text.
    Returns JSON with fields: concepts: [..], relationships: [{source, relation, target}, ...]
    """
    global _stored_text
    text = _stored_text
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text available. Please extract text first from Home page.")

    try:
        # keep prompt length limits in mind — gemini_client handles truncation
        concepts_json = extract_concepts_from_text(text)
        return {"concepts": concepts_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept extraction failed: {str(e)}")
