from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Luma - AI Learning Platform")

# Allow CORS from frontend (React)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include core routes (minimal interview-friendly setup)
# -----------------------------
from Routes import extract, quiz, chat, warmup
from Routes import advanced_chat, notes

# Core features
app.include_router(warmup.router, tags=["system"])
app.include_router(extract.router, tags=["extract"])
app.include_router(chat.router, tags=["chat"])
app.include_router(advanced_chat.router, tags=["advanced-chat"])
app.include_router(quiz.router, tags=["quiz"])
app.include_router(notes.router, tags=["notes"])

# Removed features (kept in repo but not exposed):
# - learning_path (ML recommendations - too complex for interviews)
# - concept_detail (redundant with chat)
# - concepts, index_text, rag_chat (legacy routes)

# -----------------------------
# Root route
# -----------------------------
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Luma backend running with RAG and ML support"}
