#!/usr/bin/env python3
"""
Download and verify required models for SupaQuery
"""

import os
import sys
from pathlib import Path


def download_whisper_model():
    """Download Whisper model"""
    print("📥 Downloading Whisper model...")
    try:
        import whisper
        model = whisper.load_model("tiny")
        print("✅ Whisper tiny model downloaded")
        return True
    except Exception as e:
        print(f"❌ Error downloading Whisper: {e}")
        return False


def download_embedding_model():
    """Download sentence transformer embedding model"""
    print("📥 Downloading embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        # Use model name without prefix for proper caching
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        print("✅ Embedding model downloaded and cached locally")
        return True
    except Exception as e:
        print(f"❌ Error downloading embedding model: {e}")
        return False


def check_ollama():
    """Check if Ollama is running and has required models"""
    print("🔍 Checking Ollama...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            print(f"✅ Ollama is running with models: {model_names}")
            
            if "llama3.2:latest" not in model_names:
                print("⚠️  llama3.2:latest not found. Run: ollama pull llama3.2:latest")
            
            return True
        else:
            print("⚠️  Ollama is not running. Start it with: ollama serve")
            return False
    except Exception as e:
        print(f"⚠️  Could not connect to Ollama: {e}")
        print("   Make sure Ollama is installed and running: ollama serve")
        return False


def main():
    """Main setup function"""
    print("🚀 SupaQuery Model Setup\n")
    
    success = True
    
    # Check Python dependencies
    try:
        import whisper
        import sentence_transformers
        import llama_index
        print("✅ Python dependencies installed\n")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt\n")
        sys.exit(1)
    
    # Download models
    if not download_whisper_model():
        success = False
    
    if not download_embedding_model():
        success = False
    
    if not check_ollama():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("✅ All models are ready!")
    else:
        print("⚠️  Some models need attention")
    print("="*50)
    
    print("\n💡 Quick start:")
    print("   1. Start Ollama: ollama serve")
    print("   2. Pull model: ollama pull llama3.2:latest")
    print("   3. Start backend: cd backend && python main.py")
    print("   4. Start frontend: cd frontend && npm run dev")


if __name__ == "__main__":
    main()
