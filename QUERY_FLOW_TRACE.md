# Query Processing Flow: Frontend → Backend → RAG → Claude → Frontend

## Complete Flow Diagram

```
USER (Frontend)
    ↓
[1] User types query in chat box
    ↓
[2] sendMessage() in script.js
    ↓
    POST /api/query
    {
        "query": "user question",
        "session_id": "optional_session_id"
    }
    ↓
    ===================== BACKEND =====================
    ↓
[3] FastAPI app.py receives POST @ /api/query
    └─ Validates QueryRequest (query + session_id)
    ↓
[4] RAGSystem.query(query, session_id)
    └─ Entry point to RAG pipeline
    ↓
[5] Session Management (Optional)
    ├─ IF session_id exists:
    │   └─ SessionManager.get_conversation_history(session_id)
    │       → Retrieves previous messages for context
    │
    └─ IF session_id is None:
        └─ Creates new session
    ↓
[6] AI Generator prepares Claude request
    ├─ System Prompt (educational assistant)
    ├─ Conversation History (if available)
    ├─ User Query
    └─ Tool Definitions (search capabilities)
    ↓
[7] Claude API Call (Anthropic)
    ├─ Model: claude-3-5-sonnet-20241022
    ├─ Parameters:
    │   - temperature: 0 (deterministic)
    │   - max_tokens: 800
    │   - tools: [CourseSearchTool]
    │   - tool_choice: "auto"
    │
    └─ Claude decides:
        ├─ Option A: Answer directly (general knowledge)
        │   → Returns response immediately
        │
        └─ Option B: Use search tool
            ↓
            [8] Search Tool Execution
                ├─ Query string converted to embedding
                │   (using SentenceTransformer)
                │
                ├─ VectorStore.search() in ChromaDB
                │   ├─ Collection: "course_content"
                │   ├─ Semantic similarity search
                │   └─ Returns top 5 matching chunks
                │
                ├─ Search results returned to Claude
                │
                └─ Claude synthesizes response
                    (without mentioning search process)
    ↓
[9] Claude Response Processing
    ├─ Extract text content
    ├─ Extract tool use metadata
    └─ Format final response
    ↓
[10] ToolManager.get_last_sources()
     └─ Collects sources from search queries
     ↓
[11] Update Session History
     ├─ SessionManager.add_exchange(session_id, query, response)
     └─ Stores for future context
     ↓
[12] Return QueryResponse
     {
         "answer": "Claude's response",
         "sources": ["source1", "source2"],
         "session_id": "session_123"
     }
    ↓
    ===================== FRONTEND =====================
    ↓
[13] script.js receives response
     ├─ Updates currentSessionId
     ├─ Removes loading message
     └─ Displays assistant message with sources
    ↓
[14] addMessage(response, 'assistant', sources)
     ├─ Creates message element
     ├─ Adds source citations
     └─ Appends to chat UI
    ↓
USER sees response!
```

---

## Key Components

### Frontend (script.js)
- **sendMessage()** - Captures user input, sends POST request
- **addMessage()** - Displays messages in chat
- **currentSessionId** - Tracks conversation session

### Backend (app.py)
- **POST /api/query** - Main endpoint receiving queries
- **QueryRequest** - Validates incoming data
- **QueryResponse** - Formats outgoing response

### RAG System (rag_system.py)
- **RAGSystem.query()** - Main orchestrator
- **SessionManager** - Maintains conversation history
- **ToolManager** - Manages search tools
- **AIGenerator** - Calls Claude API

### Vector Store (vector_store.py)
- **ChromaDB** - Persistent vector database
- **SentenceTransformer** - Embedding model
- **Collections**:
  - `course_catalog` - Course metadata
  - `course_content` - Actual lesson chunks

### AI Generator (ai_generator.py)
- **Claude API** - Anthropic's Claude model
- **Tool usage** - Can call search tools
- **System prompt** - Defines assistant behavior

### Search Tools (search_tools.py)
- **CourseSearchTool** - Searches course content
- Integrates with VectorStore

### Session Manager (session_manager.py)
- **create_session()** - Generates new session
- **get_conversation_history()** - Retrieves context
- **add_exchange()** - Stores query/response pairs

---

## Data Flow Example

**User Query:** "What is RAG?"

```
1. Frontend: User types "What is RAG?" in chat
   ↓
2. sendMessage() sends:
   POST /api/query {query: "What is RAG?", session_id: null}
   ↓
3. Backend receives, creates new session_id
   ↓
4. RAGSystem.query() called
   ↓
5. Claude (with tools) receives:
   - "Answer this question about course materials: What is RAG?"
   - System prompt: educator instructions
   - Tools: course search capability
   ↓
6. Claude decision:
   - "What is RAG?" is general knowledge
   - → Answers directly WITHOUT using search tool
   ↓
7. Response: "RAG stands for Retrieval-Augmented Generation..."
   ↓
8. Frontend receives and displays response

---

**User Query:** "What was covered in lesson 5?"

```
1. Frontend: User types "What was covered in lesson 5?"
   ↓
2. sendMessage() with existing session_id
   ↓
3. Backend retrieves conversation history from session
   ↓
4. RAGSystem.query() with history context
   ↓
5. Claude receives:
   - Query + conversation history
   - Tools: search capability
   ↓
6. Claude decision:
   - "What was covered in lesson 5?" is course-specific
   - → USE search tool to find lesson 5 content
   ↓
7. CourseSearchTool executes:
   - Embeds "What was covered in lesson 5?"
   - Searches course_content collection
   - Returns top 5 matching chunks from lesson 5
   ↓
8. Claude synthesizes: "Based on the course materials, lesson 5 covered..."
   ↓
9. Sources extracted and included
   ↓
10. Frontend displays response with source citations
```

---

## Architecture Benefits

✅ **Modular** - Each component has single responsibility  
✅ **Stateful** - Sessions maintain conversation context  
✅ **Smart Tool Use** - Claude decides when to search vs. answer directly  
✅ **Semantic Search** - Vector embeddings find relevant content  
✅ **Efficient** - Chunks prevent re-processing documents  
✅ **Traceable** - Sessions track all exchanges
