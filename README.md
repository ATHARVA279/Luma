# ✨ Luma

An AI-powered learning platform that uses Retrieval-Augmented Generation (RAG) and modern web tooling to extract knowledge from web content, generate study materials, and provide an interactive study experience.

This README is detailed and reflects the current repository state (Backend + Frontend), including features, endpoints, setup, environment, and developer tips.

## 🚀 Features

### 1) Advanced RAG + Hybrid Search
- Multiple search strategies in Services:
	- TF-IDF keyword search (simple RAG)
	- BM25 probabilistic ranking
	- Hybrid Search (TF-IDF + BM25)
	- Reciprocal Rank Fusion (RRF) for combining ranked lists
- Sentence-based chunking, source metadata, and dual stores (simple and advanced)
- Warmup endpoint to check stores and readiness

### 2) Conversational Chat (Basic + Advanced)
- Basic chat: RAG-based QA with context retrieval
- Advanced chat: conversational memory, query enhancement, selectable search method (hybrid/rrf)
- Session management: list sessions, view history, clear sessions

### 3) Adaptive Learning Path (ML)
- Study and quiz performance tracking
- Topic recommendations based on cosine similarity and user history
- Stats and basic performance prediction helpers

### 4) Automated Notes & Study Materials
- Generate comprehensive study notes (summary, key points, definitions)
- Flashcards and mind map structure generation
- Quick summaries for arbitrary content

### 5) Knowledge Extraction & Indexing
- Extract clean text from URLs (BeautifulSoup + heuristics)
- Index into both simple and advanced RAG stores
- Optional concept extraction via Gemini
- Clear vector store endpoint for clean re-runs

### 6) Modern UI/UX
- React + Vite + Tailwind dark theme
- `react-toastify` notifications, `react-spinners` loaders, `lucide-react` icons
- Markdown rendering removed; responses render as plain text with preserved whitespace

## 🛠️ Tech Stack

Backend (`Backend/requirements.txt`):
- FastAPI 0.95.2, uvicorn 0.22.0
- google-generativeai 0.7.2, python-dotenv 1.0.0
- scikit-learn 1.3.0, numpy 1.24.3, rank-bm25 0.2.2
- requests 2.31.0, beautifulsoup4 4.12.2, websockets 12.0
- pydantic 1.10.12, langchain 0.0.340

Frontend (`Frontend/package.json`):
- react 18.3.1, react-dom 18.3.1
- vite 5.x, tailwindcss 3.4.x
- react-router-dom 6.22.3, axios 1.6.7
- react-toastify 11.0.5, react-spinners 0.17.0, lucide-react 0.292.0

## 📁 Project Structure

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
```

## 🔧 Installation & Setup

Prerequisites:
- Python 3.9+
- Node.js 16+
- Google Gemini API key

1) Root gitignore and environment
- A root `.gitignore` is present and ignores environment files.
- Create `Backend/.env` with your Gemini API key:

```bash
cd Backend
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

2) Backend (FastAPI)

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Notes:
- `Backend/Services/gemini_client.py` uses model `gemini-2.5-flash` and includes simple retry logic for rate limits.
- The service raises an explicit error if `GEMINI_API_KEY` is missing.

3) Frontend (React + Vite)

```bash
cd Frontend
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8000` (see `Frontend/src/api/backend.js`).

## 📊 API Endpoints

Below is a high-level map. See each file under `Backend/Routes/` for request bodies and details.

### System
- GET `/warmup` — initialize/check RAG stores and system readiness

### Extraction & Indexing (Routes/extract.py)
- POST `/extract` — extract cleaned text from URL and index into both RAG stores
- DELETE `/clear-store` — clear simple and advanced RAG stores and reset cached text

### Concepts & Details
- POST `/concept-detail` — detailed concept explanation using RAG context (Routes/concept_detail.py)
- Legacy/aux in code (may be disabled in app wiring):
	- GET `/concepts` — extract concepts from stored text (Routes/concepts.py)
	- POST `/index` — index raw text directly (Routes/index_text.py)

### Chat
- POST `/chat` — basic RAG chat (Routes/chat.py)

### Advanced Chat (with memory & hybrid search)
- POST `/chat/advanced` — chat with conversational memory and hybrid/RRF search (Routes/advanced_chat.py)
- GET `/chat/history/{session_id}` — get history
- DELETE `/chat/session/{session_id}` — clear a session
- GET `/chat/sessions` — list active sessions
- Legacy/aux in code: POST `/rag_chat` — classic RAG chat (Routes/rag_chat.py)

### Learning Path (Routes/learning_path.py)
- POST `/learning/record-study` — record a study session
- POST `/learning/record-quiz` — record quiz performance
- POST `/learning/recommendations` — personalized topic recommendations
- GET `/learning/stats/{user_id}` — aggregated learning stats
- GET `/learning/predict/{user_id}/{topic}` — predict performance

### Notes (Routes/notes.py)
- POST `/notes/generate` — comprehensive study notes (summary, key points, definitions, flashcards, mind map)
- POST `/notes/summary` — quick summary for arbitrary content
- POST `/notes/concepts` — extract key concepts from content
- GET `/notes/flashcards/{topic}` — flashcards for a topic
- GET `/notes/mind-map/{topic}` — mind map structure for a topic

### Quiz (Routes/quiz.py)
- POST `/quiz/generate` — generate MCQs from selected topics (body: `{ count, topics }`)
- GET `/quiz` — generate MCQs from all available content (`?count=n`)

## 🧠 Advanced Features Explained

### Hybrid Search (TF-IDF + BM25)
Combine keyword and probabilistic scores:

```python
hybrid_score = (alpha * tfidf_score) + ((1 - alpha) * bm25_score)
```

### Reciprocal Rank Fusion (RRF)
Merge ranked lists from multiple methods:

```python
rrf_score = Σ(1 / (k + rank_i))
```

### Conversational Memory
Session-based memory captures recent exchanges and can enhance subsequent queries prior to retrieval.

## 🧩 Frontend Pages

- Home — extract content from a URL; clear/reset store; toast confirmations
- Learn — ask questions; uses doc context primarily; allows helpful comparisons when appropriate
- Quiz — select topics; MCQs with difficulty/type badges; explanations shown after submit
- Chat — conversational interface (basic)
- Notes — generate comprehensive notes, flashcards, and mind maps

UI notes:
- Notifications: `react-toastify`
- Loaders: `react-spinners`
- Icons: `lucide-react`
- Rendering: plain text with `whitespace-pre-wrap` (markdown removed)

## ⚙️ Configuration

- Backend Gemini model: `Backend/Services/gemini_client.py`
- Frontend API base URL: `Frontend/src/api/backend.js`
- Secrets: `Backend/.env` (ignored by root `.gitignore`)

## 🧪 Troubleshooting

- "GEMINI_API_KEY not found" → ensure `Backend/.env` contains `GEMINI_API_KEY=...`
- Frequent 429/quota errors → free-tier daily limits; wait or upgrade
- Frontend cannot reach backend → verify uvicorn is running and `baseURL` matches

## 🔮 Roadmap Ideas

- Mock/stub Gemini responses for offline/local dev
- Basic pytest + httpx smoke tests for routes
- Single command to run both frontend and backend concurrently

## 📝 License

This project is for learning and portfolio purposes.

---

Built for learning and experimentation with RAG + AI-assisted study.
