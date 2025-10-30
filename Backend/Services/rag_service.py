# Backend/Services/rag_service.py
import os
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Persist directory for Chroma
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore", "chroma_db")

# Initialize embedding model (Sentence-Transformers via HuggingFace wrapper)
# This keeps everything local (no external embedding API). Model downloads first-run.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embeddings = None
_vectorstore = None

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings

def _get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = _get_embeddings()
        # create or load Chroma store
        _vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    return _vectorstore

def add_text_to_store(text: str, source: str = "unknown", chunk_size: int = 800, chunk_overlap: int = 100):
    """
    Split `text` into chunks and add to the vectorstore with metadata {source: source}.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk, metadata={"source": source}) for chunk in chunks]
    vs = _get_vectorstore()
    if len(docs) > 0:
        vs.add_documents(docs)
        vs.persist()
    return len(docs)

def retrieve_context(query: str, k: int = 4) -> List[str]:
    """
    Retrieve top-k chunk texts relevant to `query`.
    Returns list of page_content strings (ordered by relevance).
    """
    vs = _get_vectorstore()
    if vs._collection is None and len(vs._collection_names()) == 0:
        # empty store
        return []
    results = vs.similarity_search(query, k=k)
    return [r.page_content for r in results]

def clear_store():
    """
    Utility to clear the vectorstore (for testing).
    """
    vs = _get_vectorstore()
    vs.delete(delete_all=True)
    vs.persist()
