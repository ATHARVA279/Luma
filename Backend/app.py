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
# Include core routes
# -----------------------------
from Routes import extract, quiz, chat, concept_detail, warmup
from Routes import advanced_chat, learning_path, notes

app.include_router(warmup.router, tags=["system"])
app.include_router(extract.router, tags=["extract"])
app.include_router(concept_detail.router, tags=["concepts"])
app.include_router(quiz.router, tags=["quiz"])
app.include_router(chat.router, tags=["chat"])

# New advanced features
app.include_router(advanced_chat.router, tags=["advanced-chat"])
app.include_router(learning_path.router, tags=["learning"])
app.include_router(notes.router, tags=["notes"])

# Remove old routes - using RAG now
# app.include_router(concepts.router, tags=["concepts"])
# app.include_router(index_text.router, prefix="/index", tags=["index"])
# app.include_router(rag_chat.router, prefix="/rag", tags=["rag"])

# -----------------------------
# Root route
# -----------------------------
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Luma backend running with RAG and ML support"}
