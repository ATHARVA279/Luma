# ✨ Luma

An AI-powered learning platform that demonstrates **RAG (Retrieval-Augmented Generation)** and modern full-stack development. Extract content from any URL, generate AI study materials, and interact with an intelligent chat system.

**Perfect for portfolios and technical interviews** - showcases practical AI/ML skills with explainable, production-ready features.

## 🌐 Live Demo

- **Frontend:** https://project-luma.vercel.app/
- **Backend API:** https://luma-2zgh.onrender.com/

---

## 🎯 Core Features (5 Essential)

### 1️⃣ **Smart Content Extraction**
- Scrape and clean text from any URL using BeautifulSoup
- Automatic text preprocessing and chunking
- Dual vector store indexing (simple + advanced)

### 2️⃣ **AI Study Notes Generator**
- Comprehensive study materials: summaries, key points, definitions
- Flashcards for memorization
- Mind map structure generation
- Topic-based retrieval from indexed content

### 3️⃣ **Basic RAG Chat**
- Simple Q&A using TF-IDF vector retrieval
- Context-aware responses using LLM
- Source tracking for answer verification

### 4️⃣ **Advanced Chat with Hybrid Search**
- **Hybrid Retrieval**: TF-IDF + BM25 + Reciprocal Rank Fusion (RRF)
- **Conversational Memory**: Session-based context using LangChain
- Multiple search strategies (hybrid, RRF, simple)
- Session management (history, clear, list)

### 5️⃣ **Interactive Quiz Generation**
- AI-generated MCQs from content
- Difficulty levels and question types
- Topic-based filtering
- Detailed explanations for answers

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI + Uvicorn (async Python web framework)
- Google Gemini AI (LLM integration)
- scikit-learn (TF-IDF vectorization)
- rank-bm25 (probabilistic ranking)
- LangChain (conversational memory)
- BeautifulSoup (web scraping)

**Frontend:**
- React 18 + Vite (fast dev server)
- Tailwind CSS (modern styling)
- React Router (navigation)
- Axios (API client)
- react-toastify (notifications)

**Key Algorithms:**
- TF-IDF (term frequency-inverse document frequency)
- BM25 (Best Matching 25 - probabilistic ranking)
- RRF (Reciprocal Rank Fusion - rank aggregation)
- Cosine similarity (vector search)

---

## 🚀 Quick Start (Windows)

### Prerequisites
- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Node.js 16+ ([Download](https://nodejs.org/))
- **Gemini API Key** ([Get Free Key](https://ai.google.dev/))
- Git Bash or Command Prompt

### Backend Setup

```cmd
cd Backend

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Configure API key (REQUIRED)
copy .env.example .env
REM Edit .env and add your Gemini API key

REM Start server
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at: `http://127.0.0.1:8000`

**Important:** The application requires a valid Gemini API key. Get one free at [https://ai.google.dev/](https://ai.google.dev/)

### Frontend Setup

```cmd
cd Frontend

REM Install dependencies
npm install

REM Start dev server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## 📊 API Endpoints (Interview Quick Reference)

### System
- `GET /warmup` - Initialize vector stores

### Content Extraction
- `POST /extract` - Extract and index content from URL
- `DELETE /clear-store` - Clear all vector stores

### Chat
- `POST /chat` - Basic RAG chat (TF-IDF retrieval)
- `POST /chat/advanced` - Advanced chat (hybrid search + memory)
- `GET /chat/history/{session_id}` - Get conversation history
- `DELETE /chat/session/{session_id}` - Clear session
- `GET /chat/sessions` - List all sessions

### Notes
- `POST /notes/generate` - Generate study notes for topic
- `POST /notes/summary` - Quick summary
- `GET /notes/flashcards/{topic}` - Get flashcards
- `GET /notes/mind-map/{topic}` - Get mind map

### Quiz
- `POST /quiz/generate` - Generate MCQs with topic filtering
- `GET /quiz?count=n` - Generate n questions from all content

---

## 📁 Project Structure (Simplified)

```
Study AI/
├── Backend/
│   ├── app.py                          # FastAPI main application
│   ├── requirements.txt                # Python dependencies
│   ├── Routes/
│   │   ├── advanced_chat.py           # Advanced chat with memory & hybrid search
│   │   ├── chat.py                    # Basic RAG chat
│   │   ├── concept_detail.py          # Detailed concept explanations
│   │   ├── concepts.py                # Concept extraction (legacy)
│   │   ├── extract.py                 # Content extraction from URLs
│   │   ├── index_text.py              # Direct text indexing (legacy)
│   │   ├── learning_path.py           # Adaptive learning recommendations
│   │   ├── notes.py                   # Study notes generation
│   │   ├── quiz.py                    # Quiz generation with topics
│   │   ├── rag_chat.py                # Classic RAG chat (legacy)
│   │   └── warmup.py                  # System initialization
│   └── Services/
│       ├── gemini_client.py           # Gemini AI integration & retry logic
│       ├── text_cleaner.py            # Web scraping & text extraction
│       ├── note_generator.py          # AI-powered study materials
│       ├── advanced_rag_service.py    # Hybrid search (TF-IDF + BM25 + RRF)
│       ├── simple_rag_service.py      # Simple TF-IDF search
│       ├── rag_service.py             # Base RAG service
│       ├── conversational_memory.py   # LangChain conversation memory
│       └── adaptive_learning.py       # ML-based recommendations
│
├── Frontend/
│   ├── package.json                   # Node dependencies
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   ├── src/
│   │   ├── App.jsx                    # Main app with routing
│   │   ├── index.jsx                  # Entry point
│   │   ├── index.css                  # Global styles
│   │   ├── api/
│   │   │   └── backend.js             # Axios API client
│   │   ├── components/
│   │   │   ├── Navbar.jsx             # Navigation bar
│   │   │   ├── Loader.jsx             # Loading spinner
│   │   │   ├── ConceptCard.jsx        # Concept display card
│   │   │   ├── ConceptList.jsx        # List of concepts
│   │   │   ├── QuizSection.jsx        # Quiz component
│   │   │   ├── NoContentMessage.jsx   # Empty state message
│   │   │   └── ChatSection.jsx        # Chat interface component
│   │   ├── pages/
│   │   │   ├── Home.jsx               # Content extraction page
│   │   │   ├── Learn.jsx              # Q&A learning page
│   │   │   ├── Quiz.jsx               # Interactive quiz page
│   │   │   ├── Chat.jsx               # Chat interface page
│   │   │   └── Notes.jsx              # Notes generation page
│   │   └── utils/
│   │       └── contentCheck.js        # Content validation utilities
│
├── .gitignore                          # Git ignore rules (includes .env)
└── README.md                           # This file
---

## 🎓 Key Concepts Demonstrated

### 1. RAG Pipeline
- **Ingestion**: Web scraping → text cleaning → chunking
- **Indexing**: TF-IDF/BM25 vectorization → store in JSON
- **Retrieval**: Cosine similarity / hybrid search → top-k chunks
- **Generation**: LLM with context → grounded answers

### 2. Hybrid Search
```python
# Weighted combination
hybrid_score = (alpha * tfidf_score) + ((1 - alpha) * bm25_score)

# Reciprocal Rank Fusion
rrf_score = sum(1 / (k + rank_i)) for all retrieval methods
```

### 3. Prompt Engineering
Different prompts for different tasks:
- **Q&A**: "Answer using context, if not found say I don't know"
- **Notes**: "Generate summary, key points, definitions in structured format"
- **Quiz**: "Create MCQs with difficulty and explanations"

### 4. Session Management
- Per-session conversation buffers
- Query enhancement with conversation context
- Session lifecycle management

---

## 🐛 Troubleshooting

**"GEMINI_API_KEY not found"**
- Required! Create `Backend/.env` file
- Copy from `.env.example` and add your API key
- Get free key at [https://ai.google.dev/](https://ai.google.dev/)

**"Rate limit exceeded"**
- Free tier: 50 requests/day
- Wait 60 seconds between requests
- Upgrade at [https://ai.google.dev/pricing](https://ai.google.dev/pricing)

**"No content found"**
- Extract content from Home page first
- Vector stores persist in `Backend/vectorstore/` as JSON
- Use "Clear" button to reset

**Frontend can't reach backend**
- Check backend is running on `http://127.0.0.1:8000`
- Check `Frontend/src/api/backend.js` baseURL setting

---

## 📝 License

This project is for learning and portfolio purposes.

---

**Built to demonstrate practical AI/ML engineering skills for technical interviews and portfolio reviews.**

