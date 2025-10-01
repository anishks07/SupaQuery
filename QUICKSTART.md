# SupaQuery Quick Start Guide

## 🎯 Goal
Get SupaQuery running with GraphRAG, multimodal document processing, and local LLM in under 15 minutes.

## 📋 Prerequisites Checklist

Before starting, make sure you have:
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 20+ installed (`node --version`)
- [ ] Docker and Docker Compose (for Docker setup)
- [ ] At least 16GB RAM available
- [ ] 20GB free disk space

## 🚀 Installation Methods

### Method 1: Docker (Easiest - Recommended)

```bash
# 1. Clone and navigate
cd SupaQuery

# 2. Start everything
docker-compose up --build

# 3. Wait for services (2-5 minutes)
# Watch the logs for "Application startup complete"

# 4. Open your browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Ollama: http://localhost:11434
```

**First time setup:**
After services start, download the LLM model:
```bash
docker exec -it supaquery-ollama ollama pull llama3.2:latest
```

---

### Method 2: Manual Setup (More Control)

#### Step 1: Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

**Verify:**
```bash
ollama --version
```

#### Step 2: Start Ollama & Download Model

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Download model (this will take a few minutes)
ollama pull llama3.2:latest

# Verify
ollama list
# Should show: llama3.2:latest
```

#### Step 3: Set Up Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies (this will take 5-10 minutes)
pip install -r requirements.txt

# Download AI models
python download_models.py

# Create environment file
cp .env.example .env

# Start the backend
python main.py
```

**Expected output:**
```
✅ GraphRAG Service initialized
   - Embedding model: sentence-transformers/all-MiniLM-L6-v2
   - LLM: Ollama (llama3.2)
   - Vector store: ChromaDB
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Step 4: Set Up Frontend

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start the frontend
npm run dev
```

**Expected output:**
```
▲ Next.js 15.x
- Local: http://localhost:3000
```

---

## ✅ Verification

### 1. Test Backend
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "document_processor": "ready",
    "graph_rag": "ready",
    "vector_store": "ready"
  }
}
```

### 2. Test Ollama
```bash
curl http://localhost:11434/api/tags
```

Should show llama3.2 in the models list.

### 3. Test Frontend
Open http://localhost:3000 in your browser. You should see the SupaQuery interface.

---

## 🎮 First Run Tutorial

### 1. Upload a Document
- Click "Browse Files" or drag and drop a PDF/DOCX
- Watch the progress bar
- File will be processed and chunked automatically

### 2. Ask a Question
- Type in the chat: "Summarize this document"
- Wait 5-10 seconds for the LLM to respond
- You'll get an answer with citations

### 3. Try Multimodal
- Upload an image (JPG, PNG)
- Ask: "What text do you see in this image?"
- OCR will extract text and the LLM will respond

- Upload an audio file (MP3, WAV)
- Ask: "What was said in this audio?"
- Whisper will transcribe and the LLM will summarize

---

## 🐛 Common Issues & Fixes

### Issue 1: "Cannot connect to backend"

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# If not, start it:
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

### Issue 2: "Ollama connection failed"

**Solution:**
```bash
# Check if Ollama is running
ollama list

# If not:
ollama serve

# Download model if missing:
ollama pull llama3.2:latest
```

### Issue 3: "Import errors in Python"

**Solution:**
```bash
cd backend
pip install --upgrade -r requirements.txt
```

### Issue 4: "Slow LLM responses"

**Causes:**
- First query always slower (model loading)
- Large documents take longer
- Limited RAM/CPU

**Solutions:**
- Try a smaller model: `ollama pull phi:latest`
- Reduce chunk size in backend/.env
- Upgrade RAM to 16GB+

### Issue 5: "OCR not working"

**Solution:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

---

## 📊 System Status Commands

```bash
# Check all services
docker-compose ps

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Check Ollama models
ollama list

# Check disk space
df -h
```

---

## 🎯 Next Steps

Once everything is working:

1. **Customize the model:**
   - Edit `backend/.env`
   - Change `OLLAMA_MODEL` to `mistral:latest` or `phi:latest`
   - Restart backend

2. **Adjust chunk size:**
   - Edit `backend/.env`
   - Modify `CHUNK_SIZE` and `CHUNK_OVERLAP`
   - Restart backend

3. **Production deployment:**
   - Update `docker-compose.yml` for production
   - Set up reverse proxy (nginx)
   - Configure SSL certificates

---

## 💡 Tips & Best Practices

1. **Upload smaller documents first** (< 10 pages) to test
2. **Ask specific questions** for better responses
3. **Use tags** to organize documents
4. **Export conversations** regularly
5. **Monitor RAM usage** - close other apps if needed

---

## 🆘 Get Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Review the main README.md
3. Test each component individually
4. Ensure system requirements are met

---

## 📈 Performance Benchmarks

**Expected performance on recommended hardware (16GB RAM, 8-core CPU):**

- Document upload: 1-5 seconds per MB
- PDF processing: 2-10 seconds per page
- Image OCR: 1-3 seconds per image
- Audio transcription: 0.5-2x realtime
- LLM response: 3-15 seconds (first query slower)
- Subsequent queries: 2-8 seconds

---

🎉 **You're all set! Start uploading documents and chatting with your AI assistant!**

