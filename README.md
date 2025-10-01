# 🚀 SupaQuery - Offline Multimodal RAG SystemSure! Here’s a **professional, concise, and clear README description** for your **Offline Multimodal RAG System** project. I’ve written it in a way that’s suitable for GitHub or portfolio showcase:



**AI-Powered Offline Document Analysis with GraphRAG**---



SupaQuery is an intelligent document analysis platform that lets you upload various file types (PDFs, DOCX, images, audio) and interact with an AI assistant powered by GraphRAG to extract insights, answer questions, and analyze your data - completely offline.# **Offline Multimodal RAG System**



---**Description:**

The Offline Multimodal RAG System is an AI-powered offline assistant designed to **ingest, index, and query multimodal data**, including **text documents (PDF, DOCX), images, and audio recordings**. Leveraging **Retrieval-Augmented Generation (RAG)** with offline large language models (LLMs), the system provides **grounded, context-aware answers** to natural language queries while maintaining **full offline functionality** and **data privacy**.

## ✨ Features

**Key Features:**

- **📁 Multimodal Data Ingestion** - Upload PDFs, DOCX files, images (JPG, PNG, GIF, WebP), and audio recordings (MP3, WAV, OGG, M4A)

- **🧠 GraphRAG Architecture** - Advanced retrieval-augmented generation with knowledge graphs for better context understanding* **Multimodal Data Ingestion:** Upload PDFs, DOCX files, images (screenshots/photos), and audio files.

- **🔒 Fully Offline** - All processing happens locally using Ollama and open-source models* **Offline Semantic Search:** Generate embeddings for text, images, and audio to enable **cross-modal semantic retrieval** using FAISS.

- **💬 Interactive Chat Interface** - Natural language conversation with your documents* **LLM-Powered Query Responses:** Provide **grounded answers or summaries** with references to source files via **offline LLaMA / MPT models**.

- **🏷️ Smart Organization** - Tag and categorize uploaded files* **Citation Transparency:** Every answer includes **numbered citations** linking back to the original document, image, or audio segment.

- **🎨 Beautiful UI** - Modern, responsive interface with dark/light mode* **Role-Based Access Control (RBAC):** Secure user authentication with **Admin, User, and Viewer roles**, ensuring access control even offline.

- **📊 Document Citations** - Every answer includes references to source documents* **Interactive Chat Interface:** Conversational UI for users to submit queries and receive AI-generated responses.

- **🔄 Real-time Processing** - See upload and processing progress live* **Optional Enhancements:** Voice-based queries, PDF/Word export of results, tagging/categorization, and highlighting matched content.



---**Tech Stack:**



## 🚀 Quick Start* **Backend:** Python, FastAPI

* **Database:** PostgreSQL

### Option 1: Docker (Recommended)* **Vector Store:** FAISS for embedding indexing and search

* **LLM Models:** LLaMA 7B (4-bit quantized), MPT-7B, Dia / OpenLLaMA 3B

```bash* **Embeddings:** `all-MiniLM-L6-v2` (text), CLIP ViT-B/32 (image)

# Clone the repository* **Speech-to-Text:** Whisper Tiny / Base (audio)

git clone https://github.com/anishks07/SupaQuery.git* **Frontend:** React / Streamlit for interactive UI

cd SupaQuery* **Deployment:** Fully offline, Dockerized



# Start all services with Docker Compose**Use Case:**

docker-compose up --buildThis system is ideal for environments where **data privacy is critical**, including **research organizations, intelligence agencies, or offline enterprise solutions**. It enables users to **search and summarize information across multiple data formats quickly**, without relying on cloud services.



# Wait for services to start, then visit:**Getting Started:**

# Frontend: http://localhost:3000

# Backend API: http://localhost:80001. Clone the repository

```2. Set up Python virtual environment and install dependencies

3. Run the backend API (FastAPI)

### Option 2: Manual Setup4. Start the frontend interface (React / Streamlit)

5. Upload your files and start querying

#### 1. Install Ollama and Download Models

**Note:** All models are **offline and pre-downloaded**, ensuring the system works without internet access.

```bash

# Run the setup script---

chmod +x setup.sh

./setup.shIf you want, I can also **add a “Features Diagram + Data Flow” section** and **badge-style highlights** to make this README **look very professional and hackathon-ready**.



# Or manually:
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull the model (in another terminal)
ollama pull llama3.2:latest
```

#### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download models
python download_models.py

# Copy environment file
cp .env.example .env

# Start the backend
python main.py
```

Backend available at: `http://localhost:8000`

#### 3. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start the development server
npm run dev
```

Frontend available at: `http://localhost:3000`

---

## 🛠️ Tech Stack

### Frontend
- Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion

### Backend
- FastAPI, Python 3.11+, LlamaIndex, ChromaDB
- PyPDF, python-docx, Tesseract OCR, OpenAI Whisper
- Ollama (llama3.2, mistral, phi)

---

## 📖 Usage

1. **Upload** - Drag and drop files or click "Browse Files"
2. **Tag** - Add custom tags to organize your documents
3. **Chat** - Ask questions about your uploaded content
4. **Export** - Download your conversation history

---

## 🔧 Configuration

### Backend (`.env`)
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
WHISPER_MODEL=base
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up --build
```

---

## 🔍 Troubleshooting

### Ollama Issues
```bash
# Check Ollama status
ollama list

# Restart Ollama
ollama serve

# Pull model
ollama pull llama3.2:latest
```

### Backend Issues
```bash
# Reinstall dependencies
cd backend
pip install --upgrade -r requirements.txt

# Test backend
curl http://localhost:8000/api/health
```

### OCR Not Working
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

---

## 📚 API Endpoints

### Backend (`http://localhost:8000`)
- `GET /` - Health check
- `POST /api/upload` - Upload files
- `POST /api/chat` - Query documents
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document

---

## 📁 Project Structure

```
SupaQuery/
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── services/     # GraphRAG, document processing
│   │   └── models/       # Data models
│   ├── main.py
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── src/app/         # Pages and API routes
│   └── src/components/  # React components
├── docker-compose.yml
└── setup.sh
```

---

## 🙏 Credits

- **LlamaIndex** - RAG framework
- **Ollama** - Local LLM inference
- **OpenAI Whisper** - Speech-to-text
- **ChromaDB** - Vector storage
- **shadcn/ui** - UI components

---

Built with ❤️ for offline AI-powered document analysis 🚀

