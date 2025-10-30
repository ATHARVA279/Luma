# Backend/Services/advanced_rag_service.py
"""
Advanced RAG with Hybrid Search combining:
- TF-IDF (keyword-based)
- BM25 (probabilistic ranking)
- Reciprocal Rank Fusion for combining results
"""
import os
import json
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import numpy as np

# Storage
PERSIST_FILE = os.path.join(os.path.dirname(__file__), "..", "vectorstore", "advanced_store.json")
_documents = []  # List of {"content": str, "source": str, "metadata": dict}
_tfidf_vectorizer = None
_tfidf_matrix = None
_bm25 = None

def _ensure_storage_dir():
    os.makedirs(os.path.dirname(PERSIST_FILE), exist_ok=True)

def _load_documents():
    """Load documents from disk"""
    global _documents
    _ensure_storage_dir()
    if os.path.exists(PERSIST_FILE):
        with open(PERSIST_FILE, 'r', encoding='utf-8') as f:
            _documents = json.load(f)
    return _documents

def _save_documents():
    """Save documents to disk"""
    _ensure_storage_dir()
    with open(PERSIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(_documents, f, indent=2)

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Smart text chunking with sentence preservation"""
    # Split by sentences first
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            # Keep overlap
            overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
            current_chunk = overlap_sentences
            current_size = sum(len(s) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def _rebuild_indexes():
    """Rebuild both TF-IDF and BM25 indexes"""
    global _tfidf_vectorizer, _tfidf_matrix, _bm25
    
    if not _documents:
        _tfidf_vectorizer = None
        _tfidf_matrix = None
        _bm25 = None
        return
    
    texts = [doc["content"] for doc in _documents]
    
    # Build TF-IDF index
    _tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(texts)
    
    # Build BM25 index
    tokenized_corpus = [doc.lower().split() for doc in texts]
    _bm25 = BM25Okapi(tokenized_corpus)

def add_text_to_store(text: str, source: str = "unknown", metadata: Dict = None) -> int:
    """
    Split text into chunks and add to store with metadata.
    Returns number of chunks added.
    """
    global _documents
    _load_documents()
    
    chunks = _chunk_text(text)
    
    for i, chunk in enumerate(chunks):
        _documents.append({
            "content": chunk,
            "source": source,
            "metadata": metadata or {},
            "chunk_id": i
        })
    
    _save_documents()
    _rebuild_indexes()
    
    return len(chunks)

def hybrid_search(query: str, k: int = 4, alpha: float = 0.5) -> List[Dict]:
    """
    Hybrid search combining TF-IDF and BM25 with Reciprocal Rank Fusion.
    alpha: weight for TF-IDF (1-alpha for BM25)
    Returns list of dicts with content, score, and metadata
    """
    global _tfidf_vectorizer, _tfidf_matrix, _bm25
    
    _load_documents()
    
    if not _documents:
        return []
    
    # Handle empty query - return random sample
    if not query or len(query.strip()) < 3:
        num_to_return = min(k, len(_documents))
        results = []
        for doc in _documents[:num_to_return]:
            results.append({
                "content": doc["content"],
                "score": 1.0,
                "source": doc.get("source", "unknown"),
                "metadata": doc.get("metadata", {})
            })
        return results
    
    # Rebuild indexes if needed
    if _tfidf_vectorizer is None:
        _rebuild_indexes()
    
    # TF-IDF search
    query_vec = _tfidf_vectorizer.transform([query])
    tfidf_scores = cosine_similarity(query_vec, _tfidf_matrix)[0]
    
    # BM25 search
    tokenized_query = query.lower().split()
    bm25_scores = _bm25.get_scores(tokenized_query)
    
    # Normalize scores to 0-1 range
    if tfidf_scores.max() > 0:
        tfidf_scores = tfidf_scores / tfidf_scores.max()
    if bm25_scores.max() > 0:
        bm25_scores = bm25_scores / bm25_scores.max()
    
    # Combine scores with weighted sum
    combined_scores = alpha * tfidf_scores + (1 - alpha) * bm25_scores
    
    # Get top-k indices
    top_indices = np.argsort(combined_scores)[-k:][::-1]
    
    # Build results
    results = []
    for idx in top_indices:
        results.append({
            "content": _documents[idx]["content"],
            "score": float(combined_scores[idx]),
            "source": _documents[idx].get("source", "unknown"),
            "metadata": _documents[idx].get("metadata", {}),
            "tfidf_score": float(tfidf_scores[idx]),
            "bm25_score": float(bm25_scores[idx])
        })
    
    return results

def reciprocal_rank_fusion(query: str, k: int = 4) -> List[Dict]:
    """
    Advanced fusion using Reciprocal Rank Fusion (RRF)
    Gets separate rankings from TF-IDF and BM25, then combines them
    """
    _load_documents()
    
    if not _documents or not query or len(query.strip()) < 3:
        return hybrid_search(query, k)
    
    if _tfidf_vectorizer is None:
        _rebuild_indexes()
    
    # Get separate rankings
    query_vec = _tfidf_vectorizer.transform([query])
    tfidf_scores = cosine_similarity(query_vec, _tfidf_matrix)[0]
    tfidf_ranking = np.argsort(tfidf_scores)[::-1]
    
    tokenized_query = query.lower().split()
    bm25_scores = _bm25.get_scores(tokenized_query)
    bm25_ranking = np.argsort(bm25_scores)[::-1]
    
    # RRF scoring
    rrf_scores = {}
    k_constant = 60  # RRF constant
    
    for rank, idx in enumerate(tfidf_ranking):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k_constant + rank + 1)
    
    for rank, idx in enumerate(bm25_ranking):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k_constant + rank + 1)
    
    # Get top-k by RRF score
    sorted_indices = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]
    
    results = []
    for idx, score in sorted_indices:
        results.append({
            "content": _documents[idx]["content"],
            "score": float(score),
            "source": _documents[idx].get("source", "unknown"),
            "metadata": _documents[idx].get("metadata", {})
        })
    
    return results

def clear_store():
    """Clear all stored documents"""
    global _documents, _tfidf_vectorizer, _tfidf_matrix, _bm25
    _documents = []
    _tfidf_vectorizer = None
    _tfidf_matrix = None
    _bm25 = None
    if os.path.exists(PERSIST_FILE):
        os.remove(PERSIST_FILE)

def get_store_info() -> Dict:
    """Get information about the store"""
    _load_documents()
    return {
        "total_chunks": len(_documents),
        "sources": list(set(doc["source"] for doc in _documents)),
        "search_methods": ["tfidf", "bm25", "hybrid", "rrf"],
        "index_status": "ready" if _tfidf_vectorizer is not None else "not_built"
    }
