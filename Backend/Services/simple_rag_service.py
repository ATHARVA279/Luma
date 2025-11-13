"""
Simple RAG service using TF-IDF and keyword matching instead of embeddings.
Multi-user support with session-based storage.
"""
import os
import json
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")

_session_cache = {}

def _ensure_storage_dir():
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

def _get_persist_file(session_id: str) -> str:
    return os.path.join(VECTORSTORE_DIR, f"simple_store_{session_id}.json")

def _load_documents(session_id: str):
    _ensure_storage_dir()
    persist_file = _get_persist_file(session_id)
    
    if os.path.exists(persist_file):
        with open(persist_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def _save_documents():
    _ensure_storage_dir()
    with open(PERSIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(_documents, f, indent=2)

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def _rebuild_index():
    """Rebuild TF-IDF index from documents"""
    global _vectorizer, _tfidf_matrix
    if not _documents:
        _vectorizer = None
        _tfidf_matrix = None
        return
    
    texts = [doc["content"] for doc in _documents]
    _vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    _tfidf_matrix = _vectorizer.fit_transform(texts)

def add_text_to_store(text: str, source: str = "unknown", chunk_size: int = 800, chunk_overlap: int = 100) -> int:
    """
    Split text into chunks and add to store.
    Returns number of chunks added.
    """
    global _documents
    _load_documents()
    
    chunks = _chunk_text(text, chunk_size, chunk_overlap)
    
    for chunk in chunks:
        _documents.append({
            "content": chunk,
            "source": source
        })
    
    _save_documents()
    _rebuild_index()
    
    return len(chunks)

def retrieve_context(query: str, k: int = 4) -> List[str]:
    """
    Retrieve top-k chunk texts relevant to query using TF-IDF similarity.
    If query is empty or very short, returns random sample of all chunks.
    """
    global _vectorizer, _tfidf_matrix
    
    _load_documents()
    
    if not _documents:
        return []
    
    # If query is empty or too short, return random sample of chunks
    if not query or len(query.strip()) < 3:
        # Return all chunks (or up to k chunks)
        num_to_return = min(k, len(_documents))
        return [doc["content"] for doc in _documents[:num_to_return]]
    
    # Rebuild index if needed
    if _vectorizer is None:
        _rebuild_index()
    
    # Transform query
    query_vec = _vectorizer.transform([query])
    
    # Calculate similarities
    similarities = cosine_similarity(query_vec, _tfidf_matrix)[0]
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[-k:][::-1]
    
    # Return top chunks (even with 0 similarity if nothing else available)
    results = []
    for idx in top_indices:
        results.append(_documents[idx]["content"])
    
    return results

def clear_store():
    """Clear all stored documents"""
    global _documents, _vectorizer, _tfidf_matrix
    _documents = []
    _vectorizer = None
    _tfidf_matrix = None
    if os.path.exists(PERSIST_FILE):
        os.remove(PERSIST_FILE)

def get_store_info() -> Dict:
    """Get information about the store"""
    _load_documents()
    return {
        "total_chunks": len(_documents),
        "sources": list(set(doc["source"] for doc in _documents))
    }
