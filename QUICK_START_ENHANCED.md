# 🚀 Quick Start Guide - Enhanced SupaQuery

## ⚡ Get Started in 5 Minutes

This guide will get you up and running with the new enhanced features immediately.

---

## 📋 Prerequisites Check

Before starting, make sure you have:

- ✅ Python 3.13 installed
- ✅ Node.js and npm installed
- ✅ PostgreSQL running
- ✅ Memgraph running (Docker)
- ✅ Ollama with llama3.2 model
- ✅ FFmpeg installed (for audio processing)

---

## 🔧 Step 1: Install Dependencies (if needed)

### Backend
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

---

## 🚀 Step 2: Start the Services

### Terminal 1: Start Backend
```bash
cd backend
source venv/bin/activate
python main.py
```

**Expected Output:**
```
🔧 Initializing Enhanced GraphRAG with Multi-Query and Evaluation...
✅ Enhanced GraphRAG initialized
   - Multi-Query Generation: Enabled
   - Evaluation Feedback: Enabled
   - Max Retries: 2
🚀 Starting SupaQuery Backend...
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 14.2.22
  - Local:        http://localhost:3000
  
✓ Ready in 2.1s
```

---

## 🎯 Step 3: First Test - Upload a Document

1. **Open browser**: http://localhost:3000
2. **Login** with your credentials
3. **Upload a test PDF**:
   - Click "Upload Files"
   - Select a PDF document
   - Wait for processing

**What happens behind the scenes:**
```
✓ Document uploaded
✓ Text extracted
✓ Chunks created with page number tracking
✓ Added to knowledge graph
✓ Entities extracted
```

---

## 💬 Step 4: Test Enhanced Features

### Test 1: Basic Query with Citations

**Ask**: "What is this document about?"

**Watch for:**
- Answer appears in chat
- Citations show at bottom with page numbers
- Quality score displayed (e.g., "✨ Quality: 85%")

**Backend logs will show:**
```
🔍 NEW QUERY: What is this document about?...
📋 Query Type: general
🎯 Routing Strategy: retrieve
📝 Generated 3 query variations:
   1. What is this document about?
   2. What does this document discuss?
   3. What is the main topic of this document?
🔎 Retrieving with 3 queries...
   Retrieved 8 unique chunks
🤖 Generating answer...
   ✓ Generated 234 chars
🔍 Evaluating answer quality...
   Overall Score: 0.87
   Sufficient: ✅ YES
```

### Test 2: Audio with Timestamps

**Upload**: An audio file (WAV, MP3)

**Ask**: "What was discussed in the audio?"

**Watch for:**
- Timestamps in citations (e.g., "🕐 02:05 - 02:25")
- Audio segments referenced

### Test 3: Greeting (Direct Reply)

**Ask**: "Hi"

**Expected**:
- Instant response (< 0.1s)
- No document search
- Backend logs show: `🎯 Routing Strategy: direct_reply`

### Test 4: Vague Query (Clarification)

**Ask**: "it"

**Expected**:
- System asks for clarification
- Backend logs show: `🎯 Routing Strategy: clarify`

### Test 5: Complex Query (Evaluation Feedback)

**Ask**: "What are all the detailed findings and conclusions?"

**Watch backend logs**:
```
🔍 Evaluating answer quality...
   Overall Score: 0.65
   Sufficient: ❌ NO
⚠️  Answer quality insufficient, preparing retry...
🔄 Attempt 2/3
   Overall Score: 0.82
   Sufficient: ✅ YES
```

**In UI**: Look for "🔄 Refined 2x"

---

## 🎨 Step 5: Explore the UI

### Citation Display

Look for this section below AI answers:

```
┌─────────────────────────────┐
│ 📄 Sources & Citations      │
├─────────────────────────────┤
│ [1] document.pdf           │
│     📄 p. 5                │
│     "The study shows..."   │
└─────────────────────────────┘

✨ Quality: 87%
```

### Click on Citations

- PDF citations show page numbers
- Audio citations show timestamps
- Text preview shows relevant excerpt

---

## 🔍 Step 6: Monitor Backend Logs

The backend logs show the entire pipeline:

```
================================================================================
🔍 NEW QUERY: What are the findings?
================================================================================
📋 Query Type: factual
🎯 Routing Strategy: retrieve

📝 Generated 3 query variations:
   1. What are the findings?
   2. What are the key results?
   3. What conclusions were reached?

🔎 Retrieving with 3 queries...
   Query 1: What are the findings?...
   Query 2: What are the key results?...
   Query 3: What conclusions were reached?...
   Retrieved 12 unique chunks

🤖 Generating answer...
   ✓ Generated 456 chars

🔍 Evaluating answer quality...
   Overall Score: 0.89
   Quality: 0.85 | Completeness: 0.92 | Relevance: 0.90
   Sufficient: ✅ YES
```

---

## 📊 Step 7: Verify Key Features

### ✅ Feature Checklist

Test each feature and check it off:

- [ ] **Multi-Query Generation**: See 2-3 queries in logs
- [ ] **Intelligent Routing**: Direct reply for "Hi"
- [ ] **Clarification**: System asks for more info on vague queries
- [ ] **PDF Citations**: Page numbers displayed (e.g., "pp. 5-6")
- [ ] **Audio Timestamps**: Time ranges shown (e.g., "02:05 - 02:25")
- [ ] **Evaluation Scores**: Quality percentage in UI
- [ ] **Retry Attempts**: "Refined 2x" shown when applicable
- [ ] **Source Preview**: Citation text previews visible
- [ ] **Fast Responses**: Non-retrieval queries < 0.5s
- [ ] **Context Awareness**: Follow-up questions work better

---

## 🐛 Quick Troubleshooting

### Problem: "No citations returned"

**Check**:
```bash
# Verify document was processed
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show document with chunks > 0
```

**Solution**: Re-upload document if chunks = 0

---

### Problem: "Evaluation always fails"

**Check**:
```bash
# Test Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello",
  "stream": false
}'
```

**Solution**: Restart Ollama or lower quality threshold

---

### Problem: "No page numbers for PDF"

**Check**: Is the PDF text-based or image-based?

**Solution**: 
- Text PDFs: Should work automatically
- Image PDFs: Need OCR (not yet implemented)

---

### Problem: "Audio timestamps missing"

**Check**:
```bash
# Verify FFmpeg installed
ffmpeg -version
```

**Solution**: Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

---

## 🎓 Next Steps

Once you've verified the basic features:

1. **Read the full documentation**:
   - `ENHANCED_ARCHITECTURE.md` - Complete architecture
   - `VISUAL_ARCHITECTURE_GUIDE.md` - Visual diagrams
   - `TESTING_ENHANCED_FEATURES.md` - Detailed testing

2. **Configure for your use case**:
   - Adjust quality threshold (default: 0.7)
   - Change retry limits (default: 2)
   - Toggle features on/off

3. **Upload more documents**:
   - Test with multiple PDFs
   - Try different audio files
   - Test with DOCX files

4. **Advanced testing**:
   - Test conversation context
   - Try complex multi-document queries
   - Test evaluation feedback loop

---

## 📈 Performance Expectations

### Response Times (Typical)

| Query Type | Time | What's Happening |
|------------|------|------------------|
| Greeting | < 0.1s | Direct reply, no processing |
| Simple query | 1-2s | Single retrieval pass |
| Complex query | 3-5s | May include retries |
| First query | +2s | Model loading |

### Quality Scores

| Score Range | Meaning | Action |
|-------------|---------|--------|
| 0.9 - 1.0 | Excellent | Accepted immediately |
| 0.7 - 0.9 | Good | Accepted |
| 0.5 - 0.7 | Fair | May trigger retry |
| < 0.5 | Poor | Will retry with expanded search |

---

## ✅ Success!

If you can:
1. ✅ Upload a document
2. ✅ Ask a question
3. ✅ See citations with page numbers/timestamps
4. ✅ See quality scores
5. ✅ Watch backend logs showing the pipeline

**Congratulations! 🎉 Your enhanced SupaQuery is working perfectly!**

---

## 🆘 Need Help?

### Check Documentation
1. `IMPLEMENTATION_COMPLETE.md` - Overview of changes
2. `ENHANCED_ARCHITECTURE.md` - Architecture details
3. `TESTING_ENHANCED_FEATURES.md` - Testing guide

### Common Issues
- Backend not starting → Check PostgreSQL and Memgraph
- No citations → Verify document upload succeeded
- Slow responses → Check Ollama is running
- No timestamps → Install FFmpeg

### Debug Mode
Enable verbose logging:
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎯 Quick Reference

### Start Everything
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Test URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Memgraph Lab: http://localhost:7687

### Key Files
- Multi-Query: `backend/app/services/multi_query_generator.py`
- Evaluation: `backend/app/services/evaluation_agent.py`
- Enhanced RAG: `backend/app/services/graph_rag_enhanced.py`
- Citations: `backend/app/services/document_processor.py`
- Frontend: `frontend/src/app/page.tsx`

---

**You're ready to explore the enhanced features! 🚀**

Happy querying! 😊
