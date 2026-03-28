# RAG Chatbot Backend - MVP Implementation

## 🎯 Overview

This is a **minimal viable product (MVP)** backend for a **RAG (Retrieval-Augmented Generation) chatbot** built with FastAPI. It provides a clean, production-ready API for:

- 📄 **Document Ingestion** - Upload and process documents
- 💬 **Chat Interface** - Ask questions and get answers
- 📝 **Chat History** - Store and retrieve conversations
- 🔄 **Ingest Tracking** - Monitor document processing
- ✅ **Error Handling** - Consistent error responses
- 🔓 **CORS Support** - Ready for React frontend

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     React Frontend                  │
│  (http://localhost:3000)            │
└────────────────┬────────────────────┘
                 │
         ┌───────▼────────┐
         │   CORS Proxy   │
         └───────┬────────┘
                 │
┌────────────────▼────────────────────┐
│   FastAPI Backend                   │
│   (http://localhost:8000)           │
├─────────────────────────────────────┤
│  Routers:                           │
│  • /api/v1/chat          (chat.py)  │
│  • /api/v1/history                  │
│  • /api/v1/ingest      (ingest_new.py)
│  • /health                          │
├─────────────────────────────────────┤
│  In-Memory Stores:                  │
│  • HistoryStore (chat messages)     │
│  • IngestStatusStore (tracking)     │
├─────────────────────────────────────┤
│  Services:                          │
│  • ChatService (RAG logic)          │
│  • IngestService (document parsing) │
├─────────────────────────────────────┤
│  Schemas (Pydantic):                │
│  • ApiResponse, ErrorResponse       │
│  • ChatRequest, ChatResponse        │
│  • ChatHistoryEntry, IngestStatus   │
└─────────────────────────────────────┘
         │                    │
    ┌────▼─────┐      ┌──────▼──────┐
    │  Ollama   │      │  data_input │
    │  LLM      │      │  documents  │
    └──────────┘      └─────────────┘
```

## 📦 Project Structure

```
Project/
├── app/
│   ├── api/
│   │   └── main.py              ← FastAPI app with routers
│   ├── routers/                 ← API endpoints
│   │   ├── __init__.py
│   │   ├── chat.py              ← Chat & history endpoints
│   │   └── ingest_new.py        ← Ingest & status endpoints
│   ├── shared/
│   │   ├── schemas/             ← Pydantic models
│   │   │   ├── common.py        (ApiResponse, ErrorResponse)
│   │   │   ├── chat.py          (ChatRequest, ChatResponse)
│   │   │   └── history.py       (ChatHistoryEntry, IngestStatus)
│   │   ├── configs/
│   │   │   └── settings.py      ← Environment config
│   │   ├── storage.py           ← In-memory stores (thread-safe)
│   │   └── utils/
│   ├── rag_core/
│   │   ├── chat_service.py      ← Main RAG logic
│   │   ├── context/             ← Retrieval
│   │   ├── llm/                 ← Ollama client
│   │   ├── prompt/              ← Prompt building
│   │   └── citation/            ← Citation generation
│   ├── data_ingest/
│   │   ├── loaders/             ← PDF/DOCX/TXT parsers
│   │   ├── parsers/             ← Document parsing
│   │   └── services/            ← IngestService
│   ├── indexing/                ← Vector indexing
│   ├── retrieval/               ← Hybrid search
│   └── ...
├── data/
│   ├── import_registry.db       ← SQLite tracking
│   └── index_store.json         ← Vector embeddings
├── data_input/                  ← Documents to ingest
│   ├── Part1-4_Minh_VN.md
│   ├── example.pdf
│   └── ...
├── requirements.txt             ← Python dependencies
├── .env.example                 ← Environment template
├── .env                         ← (Your configuration)
├── MVP_API_GUIDE.md             ← Original guide
├── MVP_API_GUIDE_EXTENDED.py    ← Comprehensive guide
├── test_api_comprehensive.py    ← Testing suite
└── README_MVP.md                ← This file
```

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python3.11 --version

# Ollama (local LLM)
# Download from https://ollama.ai
ollama --version

# Pull required model
ollama pull llama3.1:8b
```

### Setup

```bash
# 1. Navigate to project
cd Project

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env if needed (optional for MVP)

# 5. Ensure Ollama is running (separate terminal)
ollama serve

# 6. Run server
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {
#   "status": "ok",
#   "service": "rag-chatbot-api",
#   "model": "llama3.1:8b",
#   "timestamp": "2024-01-15T10:30:00Z"
# }
```

## 📡 API Endpoints

### 1. Health Check

```http
GET /health
```

Verify the API is running.

### 2. Chat - Ask Question

```http
POST /api/v1/chat
Content-Type: application/json

{
  "question": "What is Anscombe quartet?",
  "top_k": 5,
  "include_citations": true
}
```

### 3. Chat History - Get All

```http
GET /api/v1/history
```

Retrieve all chat messages (latest first).

### 4. Chat History - Clear

```http
DELETE /api/v1/history
```

Delete all chat history.

### 5. Ingest - Start

```http
POST /api/v1/ingest
```

Start document ingestion from `data_input/`.

### 6. Ingest - Get Status

```http
GET /api/v1/ingest/status/{ingest_id}
```

Check ingest job status.

## 📚 Full API Documentation

See `MVP_API_GUIDE_EXTENDED.py` for comprehensive examples and documentation.

## 🧪 Testing

### Run All Tests

```bash
python test_api_comprehensive.py
```

This runs:

1. ✅ Health check
2. ✅ Ask first question (chat)
3. ✅ Get chat history (1 entry)
4. ✅ Ask second question
5. ✅ Get updated history (2 entries)
6. ✅ Start document ingest
7. ✅ Check ingest status
8. ✅ Error handling test
9. ✅ Clear history
10. ✅ Verify history cleared

### Individual Tests with curl

```bash
# Health
curl http://localhost:8000/health

# Ask question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Anscombe quartet?"}'

# Get history
curl http://localhost:8000/api/v1/history

# Clear history
curl -X DELETE http://localhost:8000/api/v1/history

# Start ingest
curl -X POST http://localhost:8000/api/v1/ingest

# Check ingest status
curl http://localhost:8000/api/v1/ingest/status/ingest_550e8400-e29b-41d4-a716
```

## 🔧 Configuration

### `.env` File

```env
# Server
APP_NAME=rag-chatbot-api
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
API_PREFIX=/api/v1

# CORS - Allow frontend
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
REQUEST_TIMEOUT_SECONDS=120

# Retrieval
RETRIEVAL_TOP_K=5
INCLUDE_CITATIONS_DEFAULT=true

# Logging
LOG_LEVEL=INFO
```

## 📊 Key Features

### ✅ Chat History (Global, In-Memory)

- Thread-safe storage with locks
- Latest messages first (reverse chronological)
- Fast retrieval (O(1) copy)
- GET /api/v1/history
- DELETE /api/v1/history
- Automatically saved after each chat

### ✅ Ingest Status Tracking

- Create ingest job ID on POST /api/v1/ingest
- Track status: pending → processing → done/failed
- GET /api/v1/ingest/status/{ingest_id}
- Timestamps for created_at and completed_at
- Thread-safe dictionary storage

### ✅ Consistent Error Handling

- Unified error response format:
  ```json
  {
    "success": false,
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable message"
    }
  }
  ```
- Global exception handlers
- Proper HTTP status codes
- Detailed error messages

### ✅ CORS Ready

- Configure allowed origins in `.env`
- Supports credentials
- All methods and headers allowed
- Perfect for React frontend

### ✅ Clean Architecture

- **Routers** - API endpoint definitions
- **Services** - Business logic
- **Schemas** - Pydantic data models
- **Storage** - In-memory state management
- **Utils** - Logging, timing, etc.

## 💾 Data Storage

### In-Memory Stores

#### HistoryStore

```python
# Thread-safe chat history
history_store.add_entry(question, answer) → ChatHistoryEntry
history_store.get_all() → List[ChatHistoryEntry]
history_store.clear() → count
history_store.get_count() → int
```

#### IngestStatusStore

```python
# Thread-safe ingest tracking
ingest_status_store.create_ingest() → ingest_id
ingest_status_store.get_status(ingest_id) → IngestStatus
ingest_status_store.mark_done(ingest_id, message)
ingest_status_store.mark_failed(ingest_id, message)
```

### Persistent Storage (Optional)

- SQLite: `data/import_registry.db` (document import tracking)
- JSON: `data/index_store.json` (vector embeddings)

## 🧩 Integration with React Frontend

### Example: Ask Question

```typescript
const chat = async (question: string) => {
  const res = await fetch("http://localhost:8000/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: 5, include_citations: true }),
  });
  return res.json();
};
```

### Example: Get History

```typescript
const getHistory = async () => {
  const res = await fetch("http://localhost:8000/api/v1/history");
  const data = await res.json();
  return data.data.messages;
};
```

### Example: Clear History

```typescript
const clearHistory = async () => {
  const res = await fetch("http://localhost:8000/api/v1/history", {
    method: "DELETE",
  });
  return res.json();
};
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services (FastAPI + Ollama)
docker-compose -f docker/docker-compose.yml up -d

# Check logs
docker-compose -f docker/docker-compose.yml logs -f api

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Environment Variables in Docker

Update `.env` before running:

```env
OLLAMA_BASE_URL=http://ollama:11434  # Use service name
CORS_ORIGINS=["http://localhost:3000"]
```

## 🐛 Troubleshooting

### Cannot Connect to Ollama

```bash
# Check if Ollama is running
ollama list

# Start Ollama
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

### No Documents Found

Place documents in `data_input/`:

```bash
ls Project/data_input/
# Should see: *.pdf, *.md, *.txt, *.docx
```

CORS Errors from Frontend

Update `.env`:

```env
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

Restart server to apply.

### Database Lock Issues

Delete and recreate:

```bash
rm data/import_registry.db
python -m uvicorn app.api.main:app --reload
```

## 📈 Performance

| Operation             | Time    |
| --------------------- | ------- |
| Health check          | < 100ms |
| Chat (simple)         | 2-5s    |
| Chat (with citations) | 5-10s   |
| Get history           | < 50ms  |
| Ingest (5 docs)       | 10-20s  |

## 🔐 Security Considerations

⚠️ **This is an MVP** - use with care:

- ❌ No authentication (single global user)
- ❌ In-memory storage (lost on restart)
- ❌ No request rate limiting
- ❌ No input validation (beyond Pydantic)
- ⚠️ CORS allows all origins (by default)

**For production:**

- ✅ Add user authentication
- ✅ Persist data to database
- ✅ Add rate limiting
- ✅ Add input sanitization
- ✅ Restrict CORS origins
- ✅ Add logging and monitoring

## 🚦 Next Steps

### Phase 2 (After MVP)

- [ ] Add WebSocket for streaming responses
- [ ] Add database persistence (PostgreSQL)
- [ ] Add user authentication (JWT)
- [ ] Add conversation threads
- [ ] Add conversation export (PDF/JSON)
- [ ] Add analytics dashboard

### Phase 3 (Production)

- [ ] Kubernetes deployment
- [ ] CDN for static assets
- [ ] Advanced monitoring (Prometheus, Grafana)
- [ ] Load balancing
- [ ] Multi-model support
- [ ] User quotas and billing

## 📝 File Changes Made

### New Files Created

- `app/shared/schemas/history.py` - History and ingest schemas
- `app/shared/storage.py` - In-memory stores (thread-safe)
- `app/routers/chat.py` - Chat & history endpoints
- `app/routers/ingest_new.py` - Ingest & status endpoints
- `MVP_API_GUIDE_EXTENDED.py` - Full API documentation
- `test_api_comprehensive.py` - Complete test suite
- `README_MVP.md` - This file

### Files Modified

- `app/api/main.py` - Updated with routers and error handlers
- `app/shared/schemas/__init__.py` - Added new schemas
- `app/shared/schemas/common.py` - Enhanced ErrorResponse
- `app/routers/__init__.py` - Export routers

## 📞 Support

For issues or questions:

1. Check `MVP_API_GUIDE_EXTENDED.py` for detailed API docs
2. Run `test_api_comprehensive.py` to verify setup
3. Check logs: `tail -f app.log`
4. Review `.env` configuration

## 📄 License

This project is part of the Conquer RAG ChatBot initiative.

---

**Version**: 1.0.0  
**Status**: MVP Ready  
**Last Updated**: 2024-01-15  
**Python**: 3.11+  
**FastAPI**: 0.115.0+
