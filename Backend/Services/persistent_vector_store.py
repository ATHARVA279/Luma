import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from bson import ObjectId
from rank_bm25 import BM25Okapi


from Database.database import get_db

class PersistentVectorStore:
    _instance = None
    _cache: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersistentVectorStore, cls).__new__(cls)
        return cls._instance

    async def _get_collection(self):
        db = await get_db()
        return db.bm25_tokens, db.vectorizer_state

    async def save_bm25_tokens(self, user_id: str, document_id: str, chunk_id: int, tokens: List[str]):
        indices_col, _ = await self._get_collection()
        
        await indices_col.update_one(
            {
                "user_id": user_id,
                "document_id": ObjectId(document_id),
                "chunk_id": chunk_id,
                "method": "bm25"
            },
            {
                "$set": {
                    "bm25_tokens": tokens,
                    "bm25_doc_length": len(tokens),
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{user_id}_") or k == user_id]
        for key in keys_to_delete:
            if "bm25" in self._cache[key]:
                del self._cache[key]["bm25"]

    async def load_bm25_index(self, user_id: str, document_id: Optional[str] = None):
        cache_key = f"{user_id}_{document_id}" if document_id else user_id
        
        if cache_key in self._cache and "bm25" in self._cache[cache_key]:
            return self._cache[cache_key]["bm25"]

        indices_col, _ = await self._get_collection()
        
        query_filter = {"user_id": user_id, "method": "bm25"}
        if document_id:
            query_filter["document_id"] = ObjectId(document_id)
        
        cursor = indices_col.find(query_filter).sort("chunk_id", 1)
        
        tokenized_corpus = []
        chunk_ids = []
        
        async for doc in cursor:
            if "bm25_tokens" in doc:
                tokenized_corpus.append(doc["bm25_tokens"])
                chunk_ids.append(doc["chunk_id"])
                
        if not chunk_ids:
            return None, []
            
        bm25 = BM25Okapi(tokenized_corpus)
        
        self._cache.setdefault(cache_key, {})["bm25"] = (bm25, chunk_ids)
        
        return bm25, chunk_ids

    async def _fetch_chunks(self, chunk_ids: List[ObjectId]) -> Dict[ObjectId, str]:
        db = await get_db()
        chunks = await db.document_chunks.find({"_id": {"$in": chunk_ids}}).to_list(length=len(chunk_ids))
        return {c["_id"]: c["text"] for c in chunks}

    async def search_bm25(self, user_id: str, query: str, k: int = 4, document_id: Optional[str] = None) -> List[Dict]:
        bm25, chunk_ids = await self.load_bm25_index(user_id, document_id)
        
        if not bm25:
            return []
            
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        top_indices = np.argsort(scores)[-k:][::-1]
        
        top_chunk_ids = []
        top_scores = []
        
        for idx in top_indices:
            if scores[idx] > 0:
                top_chunk_ids.append(chunk_ids[idx])
                top_scores.append(scores[idx])
                
        if not top_chunk_ids:
            return []
            
        content_map = await self._fetch_chunks(top_chunk_ids)
        
        results = []
        for i, chunk_id in enumerate(top_chunk_ids):
            if chunk_id in content_map:
                results.append({
                    "content": content_map[chunk_id],
                    "score": float(top_scores[i])
                })
                
        return results

    async def delete_document_index(self, user_id: str, document_id: str):
        indices_col, _ = await self._get_collection()
        await indices_col.delete_many({
            "user_id": user_id,
            "document_id": ObjectId(document_id)
        })
        
        cache_key_specific = f"{user_id}_{document_id}"
        if cache_key_specific in self._cache:
            del self._cache[cache_key_specific]
        if user_id in self._cache:
            del self._cache[user_id]
