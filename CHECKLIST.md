# 🎯 SupaQuery Deployment Checklist

Use this checklist to ensure everything is set up correctly.

## 📋 Pre-Installation Checklist

### System Requirements
- [ ] macOS, Linux, or Windows (with WSL2)
- [ ] 16GB+ RAM available
- [ ] 20GB+ free disk space
- [ ] Internet connection (for initial setup)

### Software Requirements
- [ ] Python 3.11 or higher (`python --version`)
- [ ] Node.js 20 or higher (`node --version`)
- [ ] npm or yarn (`npm --version`)
- [ ] Git (`git --version`)
- [ ] Docker & Docker Compose (optional, for Docker setup)

### System Dependencies
- [ ] Tesseract OCR installed (`tesseract --version`)
- [ ] ffmpeg installed (`ffmpeg -version`)
- [ ] libsndfile (Linux only)

## 🔧 Installation Steps

### Step 1: Install Ollama
- [ ] Download Ollama from https://ollama.com or run: `curl -fsSL https://ollama.com/install.sh | sh`
- [ ] Verify: `ollama --version`
- [ ] Start Ollama: `ollama serve` (in background or separate terminal)
- [ ] Download model: `ollama pull llama3.2:latest`
- [ ] Verify model: `ollama list` (should show llama3.2)

### Step 2: Backend Setup
- [ ] Navigate to backend: `cd backend`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate venv:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- [ ] Install dependencies: `pip install -r requirements.txt` (takes 5-10 min)
- [ ] Download models: `python download_models.py`
- [ ] Copy env file: `cp .env.example .env`
- [ ] Review settings in `.env`
- [ ] Start backend: `python main.py`
- [ ] Verify: Backend running at http://localhost:8000
- [ ] Test: `curl http://localhost:8000/api/health`

### Step 3: Frontend Setup
- [ ] Navigate to frontend: `cd frontend`
- [ ] Install dependencies: `npm install` (takes 2-5 min)
- [ ] Copy env file: `cp .env.example .env.local`
- [ ] Review `.env.local`:
  - [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Start frontend: `npm run dev`
- [ ] Verify: Frontend running at http://localhost:3000
- [ ] Open browser: http://localhost:3000

## ✅ Verification Tests

### Test 1: Backend Health Check
```bash
curl http://localhost:8000/api/health
```
Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "services": {
    "document_processor": "ready",
    "graph_rag": "ready",
    "vector_store": "ready"
  }
}
```
- [ ] Status is "healthy"
- [ ] All services show "ready"

### Test 2: Ollama Connection
```bash
curl http://localhost:11434/api/tags
```
Expected response:
```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      ...
    }
  ]
}
```
- [ ] Returns list of models
- [ ] llama3.2:latest is present

### Test 3: Frontend Loading
- [ ] Open http://localhost:3000 in browser
- [ ] Page loads without errors
- [ ] UI is visible and responsive
- [ ] No console errors in browser DevTools
- [ ] Theme toggle works (light/dark mode)

### Test 4: File Upload
- [ ] Click "Browse Files" button
- [ ] Select a small PDF or text file
- [ ] File uploads successfully
- [ ] Progress bar shows 100%
- [ ] File appears in the left panel
- [ ] Can add tags to the file

### Test 5: Chat Functionality
- [ ] Type a simple question: "Hello, how are you?"
- [ ] Click send or press Enter
- [ ] Wait for response (5-15 seconds)
- [ ] Response appears in chat
- [ ] No error messages

### Test 6: Document Query
- [ ] Upload a PDF with some text
- [ ] Wait for processing to complete
- [ ] Ask: "Summarize this document"
- [ ] Wait for response
- [ ] Response includes citations
- [ ] Citations reference the uploaded file

### Test 7: Image OCR (if applicable)
- [ ] Upload an image with text (screenshot, document photo)
- [ ] Wait for processing
- [ ] Ask: "What text do you see?"
- [ ] Response includes extracted text
- [ ] Text is reasonably accurate

### Test 8: Audio Transcription (if applicable)
- [ ] Upload a short audio file
- [ ] Wait for processing (may take longer)
- [ ] Ask: "What was said in the audio?"
- [ ] Response includes transcription
- [ ] Transcription is reasonably accurate

## 🐛 Common Issues Checklist

### Backend Issues
- [ ] Check Python version (must be 3.11+)
- [ ] Verify virtual environment is activated
- [ ] All dependencies installed without errors
- [ ] Ollama is running (`ollama list`)
- [ ] Port 8000 is not in use
- [ ] Check backend logs for errors

### Ollama Issues
- [ ] Ollama service is running
- [ ] Model is downloaded (`ollama list`)
- [ ] Can connect to http://localhost:11434
- [ ] Sufficient RAM available (8GB+ free)
- [ ] No firewall blocking port 11434

### Frontend Issues
- [ ] Node.js version is 20+
- [ ] Dependencies installed successfully
- [ ] `.env.local` file exists
- [ ] `NEXT_PUBLIC_API_URL` is correct
- [ ] Port 3000 is not in use
- [ ] Backend is running and accessible

### Performance Issues
- [ ] Close unused applications
- [ ] Check RAM usage (should have 4GB+ free)
- [ ] Try smaller model: `ollama pull phi:latest`
- [ ] Reduce chunk size in backend/.env
- [ ] Test with smaller files first

## 🐳 Docker Setup Checklist (Alternative)

- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Navigate to project root: `cd SupaQuery`
- [ ] Run: `docker-compose up --build`
- [ ] Wait for all services to start (5-10 minutes)
- [ ] Check container status: `docker-compose ps`
- [ ] All containers show "Up"
- [ ] Download model in Ollama container:
  ```bash
  docker exec -it supaquery-ollama ollama pull llama3.2:latest
  ```
- [ ] Access frontend: http://localhost:3000
- [ ] Access backend: http://localhost:8000
- [ ] All tests from above pass

## 📊 Performance Benchmarks

Test these to ensure everything is working optimally:

- [ ] Small PDF (< 1MB): Uploads and processes in < 10 seconds
- [ ] Medium PDF (5MB): Processes in < 30 seconds
- [ ] Image with text: OCR completes in < 5 seconds
- [ ] Short audio (1 min): Transcribes in < 30 seconds
- [ ] First chat query: Responds in < 20 seconds
- [ ] Subsequent queries: Respond in < 10 seconds
- [ ] UI is responsive (no lag when typing)

## 🎓 Feature Validation

### Document Processing
- [ ] Can upload PDF files
- [ ] Can upload DOCX files
- [ ] Can upload images (JPG, PNG)
- [ ] Can upload audio (MP3, WAV)
- [ ] Files are chunked appropriately
- [ ] Chunks are searchable

### RAG Functionality
- [ ] Queries return relevant information
- [ ] Responses include citations
- [ ] Citations link to source documents
- [ ] Multiple documents can be queried together
- [ ] Context is maintained across queries

### UI Features
- [ ] Dark/light theme toggle works
- [ ] File tagging works
- [ ] Tag removal works
- [ ] File removal works
- [ ] Chat history persists in session
- [ ] Export conversation works
- [ ] Mobile responsive (test on phone)

## 📝 Final Configuration

### Optimization Settings (backend/.env)
- [ ] OLLAMA_MODEL set to preferred model
- [ ] CHUNK_SIZE appropriate for use case (512 recommended)
- [ ] CHUNK_OVERLAP set (50 recommended)
- [ ] WHISPER_MODEL set (base recommended)

### Production Ready
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Documentation reviewed
- [ ] Backup strategy in place (if needed)

## 🚀 Ready to Use!

Once all checkboxes are marked:
- ✅ Your SupaQuery system is fully operational
- ✅ You can process multimodal documents
- ✅ GraphRAG is working with citations
- ✅ Local LLM is responding correctly
- ✅ Everything is running offline

---

**Troubleshooting:**
If any check fails, refer to:
1. QUICKSTART.md - Step-by-step setup guide
2. README.md - Comprehensive documentation
3. IMPLEMENTATION_SUMMARY.md - Architecture details

**Need Help?**
- Check backend logs: `docker-compose logs backend`
- Check frontend logs: `docker-compose logs frontend`
- Test components individually
- Review error messages carefully

---

🎉 **Enjoy your offline multimodal RAG system!**

