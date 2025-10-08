# SupaQuery - Documentation Index

**Last Updated:** October 8, 2025  
**Project Status:** ✅ Production Ready

---

## 📚 Documentation Files

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| **ARCHITECTURE_UPDATED.md** | Complete system architecture with implementation details | Oct 8, 2025 |
| **VISUAL_WORKFLOWS_MERMAID.md** | Visual diagrams using Mermaid syntax | Oct 8, 2025 |
| **PERFORMANCE_OPTIMIZATIONS.md** | Recent bug fixes and performance improvements | Oct 8, 2025 |
| **ARCHITECTURE.md** | Original architecture documentation (legacy) | Earlier |
| **PROJECT_OVERVIEW.md** | Project overview and getting started | Earlier |
| **DATABASE.md** | PostgreSQL schema details | Earlier |
| **TESTING_GUIDE.md** | Testing procedures | Earlier |

---

## 🎯 Quick Navigation

### For Developers

**Getting Started:**
1. Read `PROJECT_OVERVIEW.md` for quick setup
2. Review `ARCHITECTURE_UPDATED.md` for system understanding
3. Check `PERFORMANCE_OPTIMIZATIONS.md` for recent changes
4. View `VISUAL_WORKFLOWS_MERMAID.md` for visual flows

**Implementation Details:**
- **Backend Services:** See `ARCHITECTURE_UPDATED.md` → Component Details
- **Frontend Components:** See `ARCHITECTURE_UPDATED.md` → Component Details
- **API Endpoints:** See `ARCHITECTURE_UPDATED.md` → API Reference
- **Database Schema:** See `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 7

**Data Flows:**
- **Upload Flow:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 3
- **Query Flow:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 4
- **Auth Flow:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 2

---

## 🏗️ System Overview (Quick Reference)

### Technology Stack

```
Frontend:  Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
Backend:   FastAPI + Python 3.13
Database:  PostgreSQL (structured) + Memgraph (graph)
AI/ML:     Ollama (llama3.2) + spaCy + Whisper + Tesseract
Auth:      JWT with RBAC
```

### Key Features

✅ Multi-format document processing (PDF, DOCX, images, audio)  
✅ Knowledge graph with entity extraction  
✅ Multi-query expansion for better retrieval  
✅ Answer quality evaluation with retry logic  
✅ Role-based access control (RBAC)  
✅ Document sharing between users  
✅ Chat session management  
✅ Real-time processing with progress tracking

---

## 📊 Architecture Diagrams

### 1. System Architecture
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 1
- **Shows:** Frontend, Backend, Storage, AI layers and their interactions

### 2. Authentication Flow
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 2
- **Shows:** Login process, JWT generation, token validation

### 3. Document Upload Flow
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 3
- **Shows:** Complete upload pipeline from user to knowledge graph

### 4. Query Processing Flow
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 4
- **Shows:** GraphRAG query routing, retrieval, and answer generation

### 5. Knowledge Graph Structure
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 5
- **Shows:** Node types, relationships, and Cypher query examples

### 6. RBAC Permission Flow
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 6
- **Shows:** Permission checking and role-based access control

### 7. Database Schema
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 7
- **Shows:** PostgreSQL table relationships (ERD)

### 8. Component Interaction
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 8
- **Shows:** How all components interact with each other

### 9. File Processing Pipeline
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 9
- **Shows:** Document processing flow for different file types

### 10. Query Optimization
- **Location:** `VISUAL_WORKFLOWS_MERMAID.md` → Diagram 10
- **Shows:** Decision tree for query optimization

---

## 🔧 Recent Changes (October 8, 2025)

### Bug Fixes
1. **PDF Processing Error** - Fixed "document closed" bug
   - File: `backend/app/services/document_processor.py`
   - Change: Store page count before closing document

### Performance Improvements
1. **Ollama Timeout** - 60s → 120s
2. **Context Length** - 6K → 12K chars
3. **Answer Context** - 3K → 8K chars
4. **Smart Query Detection** - Skip multi-query for simple questions

### Impact
- PDF uploads: 100% success rate
- Simple queries: 70% faster (15s vs 40s)
- Complex queries: No more timeouts
- Answer quality: Improved with more context

**Details:** See `PERFORMANCE_OPTIMIZATIONS.md`

---

## 🔑 Key Concepts

### GraphRAG (Retrieval-Augmented Generation)
Combines:
- **Graph Database:** Entity relationships and connections
- **Vector Search:** Semantic similarity via embeddings
- **LLM Generation:** Natural language answers with citations

### Multi-Query Expansion
- Generates 2-3 query variations for complex questions
- Skips expansion for simple questions (optimization)
- Deduplicates results across queries

### Answer Quality Evaluation
- Scores: Quality (0-1), Completeness (0-1), Relevance (0-1)
- Threshold: 0.7 overall score
- Retry: Up to 3 attempts with improved strategy

### RBAC (Role-Based Access Control)
- **Roles:** Admin, User, Viewer
- **Permissions:** Granular (documents:*, chat:*, users:*, roles:*)
- **Enforcement:** JWT + decorator-based checks

---

## 🚀 Getting Started

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/anishks07/SupaQuery.git
cd SupaQuery

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Database setup
createdb supaquery
docker run -p 7687:7687 -p 3000:3000 memgraph/memgraph-platform

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Start backend
python main.py

# 6. Frontend setup (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local

# 7. Start frontend
npm run dev
```

### Access Points
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Memgraph Lab:** http://localhost:3001

---

## 📖 API Quick Reference

### Authentication
```bash
# Register
POST /api/auth/register
{username, email, password, full_name}

# Login
POST /api/auth/login
{username, password}
→ Returns JWT token

# Get current user
GET /api/users/me
Authorization: Bearer {token}
```

### Documents
```bash
# Upload files
POST /api/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
Body: files[], is_public

# List documents
GET /api/documents?include_shared=true
Authorization: Bearer {token}

# Delete document
DELETE /api/documents/{id}
Authorization: Bearer {token}
```

### Chat
```bash
# Send query
POST /api/chat
Authorization: Bearer {token}
{message, document_ids, session_id}
→ Returns answer with citations

# List sessions
GET /api/chat/sessions
Authorization: Bearer {token}
```

---

## 🔍 Troubleshooting

### Common Issues

**1. PDF Upload Fails**
- ✅ FIXED: October 8, 2025
- Make sure you're using the latest code

**2. Query Timeout**
- ✅ FIXED: Timeout increased to 120s
- Complex queries may take 30-60s

**3. Old Data in Responses**
- Run cleanup script: `python cleanup_knowledge_graph.py`
- Choose option 1 (Smart Cleanup)

**4. Authentication Errors**
- Check JWT token hasn't expired (30min)
- Verify token is in localStorage
- Check backend logs for validation errors

**5. Memgraph Connection Issues**
- Ensure Memgraph is running: `docker ps | grep memgraph`
- Check port 7687 is available
- Restart Memgraph container if needed

---

## 📊 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Login | < 200ms | JWT generation |
| File Upload | 2-10s | Depends on file size |
| PDF Processing | 1-3s | Per MB |
| Simple Query | 10-15s | "what are", "how many" |
| Complex Query | 30-60s | Multi-query expansion |
| Entity Extraction | 50-100ms | Per chunk |
| Graph Query | < 100ms | Memgraph is fast |

---

## 🧪 Testing

### Run Tests
```bash
cd backend
pytest tests/

cd frontend  
npm test
```

### Manual Testing
See `TESTING_GUIDE.md` for detailed procedures:
1. Authentication flow
2. Document upload (all formats)
3. Chat queries (simple & complex)
4. Document deletion
5. RBAC permissions
6. Error handling

---

## 📝 Code Structure

### Backend (`/backend`)
```
app/
├── auth/           # Authentication & RBAC
├── database/       # PostgreSQL models & service
├── models/         # Pydantic schemas
├── services/       # Business logic
│   ├── document_processor.py
│   ├── graph_rag_enhanced.py
│   ├── entity_extractor.py
│   ├── memgraph_service.py
│   ├── evaluation_agent.py
│   └── multi_query_generator.py
└── utils/          # Helper functions

main.py             # FastAPI application
requirements.txt    # Python dependencies
```

### Frontend (`/frontend`)
```
src/
├── app/            # Next.js pages
│   ├── login/
│   ├── signup/
│   ├── api/        # API routes
│   ├── page.tsx    # Main dashboard
│   └── layout.tsx  # Root layout
├── components/     # React components
│   └── ui/         # shadcn/ui components
├── lib/            # Utilities
│   ├── AuthContext.tsx
│   └── auth.ts
└── hooks/          # Custom hooks

package.json        # Node dependencies
```

---

## 🤝 Contributing

### Before Making Changes
1. Review `ARCHITECTURE_UPDATED.md` for system understanding
2. Check `PERFORMANCE_OPTIMIZATIONS.md` for recent changes
3. Review relevant visual workflows in `VISUAL_WORKFLOWS_MERMAID.md`

### Making Changes
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with clear commit messages
3. Test thoroughly
4. Update documentation if needed
5. Submit pull request

---

## 📞 Support

### Documentation
- Architecture: `ARCHITECTURE_UPDATED.md`
- Workflows: `VISUAL_WORKFLOWS_MERMAID.md`
- Performance: `PERFORMANCE_OPTIMIZATIONS.md`
- Testing: `TESTING_GUIDE.md`

### Resources
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs
- Memgraph: https://memgraph.com/docs/
- Ollama: https://github.com/ollama/ollama

---

## 📈 Roadmap

### Short-term
- [ ] Advanced entity relationship queries
- [ ] Document comparison features
- [ ] Batch document upload
- [ ] Export chat history

### Mid-term
- [ ] Real-time collaboration
- [ ] Advanced graph visualization
- [ ] Custom LLM fine-tuning
- [ ] Mobile app

### Long-term
- [ ] Multi-language support
- [ ] Enterprise SSO integration
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment

---

**Project:** SupaQuery  
**Version:** 3.0  
**Status:** ✅ Production Ready  
**Last Audit:** October 8, 2025
