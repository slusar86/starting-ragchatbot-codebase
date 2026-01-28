# Claude Configuration for RAG Chatbot System

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) Chatbot** system that answers questions about course materials. It combines semantic search with Claude AI to provide intelligent, context-aware responses.

**Tech Stack:**
- **Backend:** Python, FastAPI, ChromaDB, Anthropic Claude API
- **Frontend:** Vanilla JavaScript, HTML, CSS
- **Vector Store:** ChromaDB with SentenceTransformer embeddings
- **AI:** Claude 3.5 Sonnet (via Anthropic API)

---

## Project Structure

```
starting-ragchatbot-codebase/
├── backend/
│   ├── app.py                  # FastAPI server & API endpoints
│   ├── rag_system.py           # Main RAG orchestrator
│   ├── vector_store.py         # ChromaDB vector database
│   ├── ai_generator.py         # Claude API integration
│   ├── document_processor.py   # Document parsing & chunking
│   ├── session_manager.py      # Conversation history
│   ├── search_tools.py         # Search tools for Claude
│   ├── models.py               # Data models
│   └── config.py               # Configuration management
├── frontend/
│   ├── index.html              # Chat interface
│   ├── script.js               # Frontend logic
│   ├── style.css               # Styling
│   ├── config.js               # Frontend Claude config (LOCAL)
│   └── claude-integration.js   # Claude frontend features
├── docs/
│   └── course*.txt             # Course materials (processed into RAG)
├── main.py                     # Entry point to build vector store
├── pyproject.toml              # Python dependencies
├── run.sh                      # Start script
└── CLAUDE.local.md             # This file (LOCAL ONLY)
```

---

## API Key Configuration

**Your Anthropic API Key:** `[REMOVED - See .env file]`

**Backend (.env file):**
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

**Frontend (config.js):**
Configure with your API key from the .env file.

---

## How the System Works

### Query Flow (User → Response)

1. **User submits query** via chat interface (frontend)
2. **Frontend sends** POST to `/api/query` with query + session_id
3. **Backend (app.py)** receives request
4. **RAGSystem** orchestrates:
   - Retrieves conversation history (if session exists)
   - Prepares Claude request with search tools
5. **Claude decides:**
   - General question? Answer directly
   - Course-specific? Use search tool
6. **If searching:**
   - Query embedded using SentenceTransformer
   - ChromaDB finds top 5 similar course chunks
   - Results sent back to Claude
7. **Claude synthesizes** response from search results
8. **Response returned** with sources and session_id
9. **Frontend displays** answer with citations

### Document Processing

Documents in `docs/` are processed:
1. Parse course metadata (title, instructor, link)
2. Split into lessons
3. Chunk text (sentence-based with overlap)
4. Embed chunks using SentenceTransformer
5. Store in ChromaDB collections:
   - `course_catalog` (metadata)
   - `course_content` (chunks)

---

## Development Commands

### **CRITICAL: Always Use `uv` for Python Execution**

This project uses `uv` as the package/environment manager. **NEVER use plain `python`, `pip`, or `pytest` commands.**

```bash
# ✅ CORRECT - Run Python scripts
uv run python script.py
uv run python main.py

# ✅ CORRECT - Start server
cd backend
uv run uvicorn app:app --reload

# ✅ CORRECT - Install dependencies
uv sync

# ✅ CORRECT - Add new packages
uv add package_name

# ✅ CORRECT - Run tests
uv run pytest

# ❌ WRONG - Don't use these
python script.py          # ❌
pip install package       # ❌
pytest                    # ❌
uvicorn app:app --reload  # ❌ (missing 'uv run')
```

### Start the System

```bash
# Quick start (builds DB + starts server)
./run.sh

# Or manually:
python main.py              # Build vector store from docs/
cd backend
uvicorn app:app --reload    # Start FastAPI server
```

### Access the Application

- **Frontend:** http://localhost:8000 (served by FastAPI)
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/courses

### Test API Endpoint

```powershell
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    query = "What is RAG?"
    session_id = $null
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/query" -Headers $headers -Body $body -Method POST | Select-Object -ExpandProperty Content
```

---

## Key Files to Work With

### Backend Files

**app.py** - API endpoints
- `POST /api/query` - Main query endpoint
- `GET /api/courses` - Get course statistics
- CORS and static file serving

**rag_system.py** - Core RAG logic
- `query()` - Main entry point for queries
- `add_course_document()` - Add new courses
- Integrates all components

**ai_generator.py** - Claude integration
- `generate_response()` - Calls Claude API
- Handles tool usage
- System prompt defines assistant behavior

**vector_store.py** - ChromaDB interface
- `search()` - Semantic search
- `add_course_content()` - Store embeddings
- Collections management

**document_processor.py** - Text processing
- `process_course_document()` - Parse course files
- `chunk_text()` - Smart text chunking
- Extracts course/lesson metadata

### Frontend Files

**script.js** - Chat logic
- `sendMessage()` - Submit queries
- `addMessage()` - Display responses
- Session management

**index.html** - UI structure
- Chat interface
- Course sidebar
- Suggested questions

---

## Working with Claude

### When to Ask Claude for Help

✅ **Debugging backend errors**
- "Why is my ChromaDB query failing?"
- "How do I fix this FastAPI CORS issue?"

✅ **Adding features**
- "Add a feature to export chat history"
- "Implement conversation branching"

✅ **Improving RAG**
- "How can I improve search relevance?"
- "Optimize chunking strategy for better results"

✅ **Understanding code**
- "Explain how the search tool works"
- "Walk me through the query flow"

### Common Tasks

**Add a new course document:**
```python
# Run main.py after adding file to docs/
python main.py
```

**Clear and rebuild database:**
```python
# In rag_system.py, use:
rag_system.add_course_folder("docs", clear_existing=True)
```

**Change Claude model:**
Edit `backend/config.py`:
```python
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
```

**Adjust chunk size:**
Edit `backend/config.py`:
```python
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200
```

---

## Environment Variables

Create `.env` in root directory:

```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RESULTS=0
MAX_HISTORY=10
CHROMA_PATH=./backend/chroma_data
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Test Individual Components
```bash
# Test vector store
pytest backend/tests/test_vector_store.py

# Test API endpoints
pytest backend/tests/test_api_endpoints.py

# Test RAG system
pytest backend/tests/test_rag_system.py
```

---

## Troubleshooting

### ChromaDB Issues
```bash
# Delete and rebuild
rm -rf backend/chroma_data
python main.py
```

### API Key Errors
- Check `.env` file exists in root
- Verify API key is valid
- Ensure no extra spaces in key

### Port Already in Use
```bash
# Change port in run.sh or:
uvicorn app:app --reload --port 8001
```

### CORS Errors
- Ensure FastAPI CORS middleware is configured
- Check frontend is accessing correct URL

---

## Architecture Insights

### Why This Design?

**Tool-based Search:** Claude decides when to search vs. answer directly
- More efficient (fewer unnecessary searches)
- Better user experience (faster general answers)
- Contextual awareness

**Session Management:** Maintains conversation history
- Multi-turn conversations
- Context preservation
- Better follow-up questions

**Chunking Strategy:** Sentence-based with overlap
- Preserves semantic meaning
- Prevents mid-sentence cuts
- Overlap ensures context continuity

**Two Collections:** Separate metadata and content
- Fast course lookup
- Efficient content search
- Flexible querying

---

## Next Steps / Enhancements

**Potential Improvements:**
1. Add conversation export functionality
2. Implement conversation branching
3. Add file upload for new courses
4. Create admin interface for course management
5. Add user authentication
6. Implement streaming responses
7. Add citation preview on hover
8. Create mobile-responsive design
9. Add analytics dashboard
10. Multi-language support

---

## Resources

- [Anthropic Claude Docs](https://docs.anthropic.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [SentenceTransformers](https://www.sbert.net)

---

## Notes for Claude

**When helping with this project:**
- Always check current file context before making changes
- Test API endpoints after backend changes
- Consider RAG performance implications
- Maintain conversation history integrity
- Keep frontend/backend API contracts in sync
- Update documentation when adding features
- Follow existing code style (Black formatting)
- Add tests for new functionality

**Project Goals:**
- Fast, accurate course material retrieval
- Natural conversation flow
- Easy to add new courses
- Clean, maintainable code
- Good user experience

**Current Status:** ✅ Fully functional RAG system with Claude AI integration
