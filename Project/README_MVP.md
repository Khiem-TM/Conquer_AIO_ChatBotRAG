# RAG ChatBot MVP Backend

A minimal, production-ready FastAPI backend for a RAG (Retrieval-Augmented Generation) ChatBot. Designed for rapid prototyping and easy integration with React frontends.

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install fastapi uvicorn pydantic

# 2. Run server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Open docs
# Browser: http://localhost:8000/docs
```

## ✨ Features

| Feature             | Status | Details                                       |
| ------------------- | ------ | --------------------------------------------- |
| **Chat API**        | ✓      | Ask questions, get answers with citations     |
| **Chat History**    | ✓      | Global history with GET/DELETE endpoints      |
| **Ingest Tracking** | ✓      | Track document processing with status IDs     |
| **Error Handling**  | ✓      | Consistent error format across all endpoints  |
| **CORS**            | ✓      | Enabled for all origins (configurable)        |
| **Persistence**     | ✓      | JSON-based storage (easy to migrate to DB)    |
| **Documentation**   | ✓      | Auto-generated Swagger UI                     |
| **Clean Code**      | ✓      | Well-organized with routers, models, services |

## 📋 API Endpoints

### System

- `GET /` - API info
- `GET /health` - Health check

### Chat

- `POST /v1/chat` - Ask a question
- `GET /v1/history` - Get all chat messages
- `DELETE /v1/history` - Clear chat history

### Ingest

- `POST /v1/ingest` - Start document ingestion
- `GET /v1/ingest/status/{ingest_id}` - Check ingest status

See `MVP_API_GUIDE.md` for detailed examples.

## 📁 Project Structure

```
app/
├── main.py              # FastAPI application
├── models/              # Pydantic models
│   ├── chat.py
│   ├── ingest.py
│   └── common.py
├── routers/             # API endpoints
│   ├── chat.py          # /v1/chat endpoints
│   └── ingest.py        # /v1/ingest endpoints
└── services/            # Business logic
    ├── __init__.py      # ChatHistoryService
    └── ingest.py        # IngestService

data/
├── chat_history.json    # Chat storage
└── ingest_status.json   # Ingest operations

examples/
├── test_api.py          # Python test script
└── react-api-example.tsx # React hook examples

docs/
├── MVP_API_GUIDE.md     # Complete API guide
├── QUICKSTART.md        # Setup guide
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

Create `.env` in project root (optional):

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# CORS (comma-separated for multiple origins)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Storage
CHAT_HISTORY_FILE=data/chat_history.json
INGEST_STATUS_FILE=data/ingest_status.json
```

### Python Code Configuration

Edit `app/main.py` to change CORS:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Usage

### 1. Run Development Server

```bash
cd Project
python -m uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`

### 2. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Test with Python

```python
import requests

# Health check
print(requests.get("http://localhost:8000/health").json())

# Send message
response = requests.post(
    "http://localhost:8000/v1/chat",
    json={
        "question": "What is AI?",
        "top_k": 5,
        "include_citations": True
    }
)
print(response.json())

# Get history
print(requests.get("http://localhost:8000/v1/history").json())
```

### 4. Test with cURL

```bash
# Health
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Python?","top_k":5,"include_citations":true}'

# History
curl http://localhost:8000/v1/history

# Clear history
curl -X DELETE http://localhost:8000/v1/history

# Ingest
curl -X POST http://localhost:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"documents":["doc1.pdf","doc2.md"]}'
```

### 5. Automated Testing

```bash
python examples/test_api.py
```

This runs through all endpoints and displays results.

## 🔗 React Integration

### 1. Copy Hook

```bash
cp examples/react-api-example.tsx ../your-react-app/src/hooks/useApi.tsx
```

### 2. Use in Component

```tsx
import { useChat } from "./hooks/useApi";

function ChatApp() {
  const { messages, loading, sendMessage, clearHistory } = useChat();

  return (
    <div>
      <input
        onKeyPress={(e) => {
          if (e.key === "Enter") sendMessage(e.target.value);
        }}
      />
      <div>
        {messages.map((msg) => (
          <div key={msg.id}>
            <p>Q: {msg.question}</p>
            <p>A: {msg.answer}</p>
          </div>
        ))}
      </div>
      <button onClick={clearHistory}>Clear</button>
    </div>
  );
}
```

### 3. Handle CORS

React (usually on port 3000) can call backend (port 8000) directly:

```tsx
const API_BASE = "http://localhost:8000"; // Development
// const API_BASE = 'https://api.yourdomain.com'  // Production
```

## 📊 Response Formats

### Success Response

```json
{
  "id": "msg_550e8400-e29b-41d4-a716-446655440000",
  "question": "What is AI?",
  "answer": "Artificial Intelligence is...",
  "timestamp": "2024-03-28T10:30:00.123456",
  "sources": [
    {
      "source_id": "doc_1",
      "source_name": "article.md",
      "score": 0.934
    }
  ],
  "latency_ms": 1234
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Question cannot be empty"
  }
}
```

## 🗄 Data Storage

### Chat History (`data/chat_history.json`)

```json
{
  "messages": [
    {
      "id": "msg_550e8400-e29b-41d4-a716-446655440000",
      "question": "What is AI?",
      "answer": "Artificial Intelligence is...",
      "timestamp": "2024-03-28T10:30:00.123456",
      "sources": []
    }
  ]
}
```

### Ingest Status (`data/ingest_status.json`)

```json
{
  "operations": {
    "ing_550e8400-e29b-41d4-a716-446655440000": {
      "id": "ing_550e8400-e29b-41d4-a716-446655440000",
      "status": "done",
      "timestamp": "2024-03-28T10:30:00.123456",
      "message": "Successfully processed 2 documents",
      "docs_processed": 2,
      "chunks_created": 200
    }
  }
}
```

## 🔌 Integration with Existing RAG

### Option 1: Use Existing ChatService

```python
# In app/routers/chat.py
from app.rag_core.chat_service import ChatService

chat_service = ChatService()

@router.post("/v1/chat")
async def chat(payload: ChatRequest) -> ChatResponse:
    # Call your existing RAG service
    response = await chat_service.ask(payload)

    # Save to history
    msg = history_service.add_message(
        question=payload.question,
        answer=response.answer,
        sources=response.citations,
    )

    return ChatResponse(...)
```

### Option 2: Stub Implementation

For testing purposes, responses are pre-populated. Replace in `app/routers/chat.py`:

```python
# From:
answer = f"Response to: {payload.question[:50]}..."

# To:
answer = await your_rag_service.query(payload.question)
```

## 🧪 Testing

### Unit Tests (Future)

```bash
# Create tests/test_chat.py
# Create tests/test_ingest.py
# Run: pytest tests/
```

### Integration Tests

```bash
python examples/test_api.py
```

### Manual Testing

Use Swagger UI at `/docs` to test all endpoints interactively.

## 📈 Performance

Expected latencies with stub implementation:

- Chat response: 10-50ms
- History retrieval: 1-10ms
- Ingest check: 1-5ms

With real RAG service:

- Chat response: 2-10s (depending on model)
- History: 10-50ms
- Ingest: 30s+ (depending on document size)

## 🔒 Security Notes

This is an MVP with **no authentication**. For production:

1. **Add Authentication**

   - JWT tokens
   - API keys
   - OAuth2

2. **Restrict CORS**

   ```python
   allow_origins=["https://yourdomain.com"]
   ```

3. **Rate Limiting**

   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   @app.post("/v1/chat")
   @limiter.limit("10/minute")
   ```

4. **Use Database**

   - Replace JSON files with SQLite/PostgreSQL
   - Add data validation

5. **HTTPS**
   - Use SSL certificates in production
   - Configure reverse proxy (Nginx)

## 🚢 Deployment

### Local Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t rag-chatbot-api .
docker run -p 8000:8000 rag-chatbot-api
```

### Docker Compose

```bash
docker-compose up
```

### Cloud Platforms

- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo
- **Render**: Deploy from GitHub
- **AWS**: EC2 + Nginx
- **Google Cloud**: Cloud Run

## 📚 Documentation

- **API Guide**: `MVP_API_GUIDE.md`
- **Quick Start**: `QUICKSTART.md`
- **Code Examples**: `examples/`
- **Auto-generated**: `/docs` (Swagger UI)

## 🛠 Development

### Add New Endpoint

1. Create model in `app/models/`
2. Create router in `app/routers/`
3. Add service logic in `app/services/`
4. Include router in `app/main.py`

Example:

```python
# models/documents.py
class DocumentList(BaseModel):
    documents: list[str]

# routers/documents.py
from fastapi import APIRouter
from app.models.documents import DocumentList

router = APIRouter(prefix="/v1", tags=["documents"])

@router.get("/documents")
async def list_documents():
    # Implementation
    pass

# main.py
from app.routers import documents
app.include_router(documents.router)
```

### Code Style

- Use type hints everywhere
- Docstrings for all functions
- Consistent naming (snake_case)
- Follow PEP 8

## 🐛 Troubleshooting

### Import Errors

```bash
# Make sure you're in correct directory
cd Project
python -m uvicorn app.main:app
```

### Port Already in Use

```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### CORS Errors

Frontend logs: `Access to XMLHttpRequest blocked by CORS policy`

Solution:

1. Check `.env` or `app/main.py` CORS config
2. Verify frontend URL is in `allow_origins`
3. Clear browser cache and cookies

### Data Doesn't Persist

Check file permissions:

```bash
ls -la data/
# Should show: -rw-r--r-- files
chmod 666 data/chat_history.json
chmod 666 data/ingest_status.json
```

## ✅ Checklist for Production

- [ ] Replace stub responses with real RAG service
- [ ] Add authentication (JWT/API keys)
- [ ] Restrict CORS to your domain
- [ ] Use database instead of JSON
- [ ] Add rate limiting
- [ ] Enable HTTPS/SSL
- [ ] Set up logging and monitoring
- [ ] Test load capacity
- [ ] Add error tracking (Sentry)
- [ ] Document API changes
- [ ] Set up CI/CD pipeline
- [ ] Create backup strategy

## 📞 Support

- See documentation at `/docs` (Swagger UI)
- Check examples in `examples/` directory
- Review test script: `examples/test_api.py`
- Read API guide: `MVP_API_GUIDE.md`

## 📄 License

Created as part of RAG ChatBot MVP project.

## 🎯 Next Steps

1. **Test it**: Run `python examples/test_api.py`
2. **Explore docs**: Visit `http://localhost:8000/docs`
3. **Integrate**: Add real RAG service
4. **Deploy**: Push to production
5. **Monitor**: Add logging and metrics

---

**Build fast, iterate often, deploy with confidence! 🚀**
