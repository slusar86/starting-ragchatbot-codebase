# Query Processing Flow Diagram

## Complete Flow (Mermaid Diagram)

```mermaid
graph TD
    A["👤 User<br/>Frontend"] -->|1. Types Query| B["💬 Chat Input<br/>script.js"]
    
    B -->|2. sendMessage<br/>POST /api/query| C["🚀 FastAPI<br/>app.py"]
    
    C -->|3. Receive QueryRequest| D["✅ Validate<br/>Query + Session"]
    
    D -->|4. Initialize| E["🎯 RAGSystem.query<br/>rag_system.py"]
    
    E -->|5a. Check Session| F{Session<br/>Exists?}
    
    F -->|YES| G["📜 Retrieve<br/>Conversation History<br/>session_manager.py"]
    F -->|NO| H["🆕 Create<br/>New Session"]
    
    G --> I["🤖 AIGenerator<br/>ai_generator.py"]
    H --> I
    
    I -->|6. Prepare Request| J["📋 Build Messages<br/>- System Prompt<br/>- History<br/>- User Query<br/>- Tools"]
    
    J -->|7. API Call| K["🌐 Claude API<br/>claude-3-5-sonnet-20241022"]
    
    K -->|8. Claude Decides| L{Use<br/>Search<br/>Tool?}
    
    L -->|General Knowledge| M["✏️ Answer Directly<br/>No Search Needed"]
    
    L -->|Course Specific| N["🔍 Search Tool<br/>search_tools.py"]
    
    N -->|9. Embed Query| O["🧠 SentenceTransformer<br/>Convert to Embedding"]
    
    O -->|10. Semantic Search| P["💾 ChromaDB<br/>vector_store.py"]
    
    P -->|11. Find Similar| Q["📚 Search Collections<br/>- course_content<br/>- course_catalog"]
    
    Q -->|12. Return Top 5| R["📖 Search Results<br/>Chunks + Metadata"]
    
    R -->|13. Send Back to Claude| K
    
    K -->|14. Synthesize| S["📝 Generate Response<br/>Using Context"]
    
    M --> T["✅ Get Sources<br/>tool_manager.get_last_sources"]
    S --> T
    
    T -->|15. Update Session| U["💾 Save Exchange<br/>session_manager.add_exchange"]
    
    U -->|16. Format Response| V["📦 QueryResponse<br/>answer + sources + session_id"]
    
    V -->|17. Return JSON| B
    
    B -->|18. Process Response| W["🎨 addMessage<br/>Display in Chat"]
    
    W -->|19. Show to User| A
    
    style A fill:#e1f5ff
    style K fill:#fff3e0
    style P fill:#f3e5f5
    style B fill:#e8f5e9
    style W fill:#fce4ec
    style M fill:#c8e6c9
    style N fill:#bbdefb
