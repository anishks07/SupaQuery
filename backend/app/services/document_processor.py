"""
Document Processor
Handles extraction and processing of different file types:
- PDF: Text extraction
- DOCX: Text extraction  
- Images: OCR using Tesseract
- Audio: Transcription using Whisper
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import mimetypes

# PDF processing
from pypdf import PdfReader

# DOCX processing
from docx import Document

# Image processing
from PIL import Image
import pytesseract

# Audio processing
import whisper
import torch

# Text chunking
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter


class DocumentProcessor:
    def __init__(self):
        """Initialize document processor with models"""
        self.whisper_model = None  # Lazy load
        self.sentence_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        
    def _load_whisper(self):
        """Lazy load Whisper model"""
        if self.whisper_model is None:
            print("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    
    async def process_file(self, file_path: str, original_filename: str, file_id: str) -> Dict[str, Any]:
        """
        Process a file based on its type
        Returns extracted text and metadata
        """
        file_path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Determine file type
        if file_path.suffix.lower() == '.pdf':
            return await self._process_pdf(file_path, file_id, original_filename)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return await self._process_docx(file_path, file_id, original_filename)
        elif mime_type and mime_type.startswith('image/'):
            return await self._process_image(file_path, file_id, original_filename)
        elif mime_type and mime_type.startswith('audio/'):
            return await self._process_audio(file_path, file_id, original_filename)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    async def _process_pdf(self, file_path: Path, file_id: str, original_filename: str) -> Dict[str, Any]:
        """Extract text from PDF"""
        try:
            reader = PdfReader(str(file_path))
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            # Chunk the text
            chunks = self._chunk_text(text)
            
            return {
                "id": file_id,
                "filename": original_filename,
                "type": "pdf",
                "text": text,
                "chunks": len(chunks),
                "chunk_data": chunks,
                "pages": len(reader.pages)
            }
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    async def _process_docx(self, file_path: Path, file_id: str, original_filename: str) -> Dict[str, Any]:
        """Extract text from DOCX"""
        try:
            doc = Document(str(file_path))
            text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # Chunk the text
            chunks = self._chunk_text(text)
            
            return {
                "id": file_id,
                "filename": original_filename,
                "type": "docx",
                "text": text,
                "chunks": len(chunks),
                "chunk_data": chunks,
                "paragraphs": len(doc.paragraphs)
            }
        except Exception as e:
            raise Exception(f"Error processing DOCX: {str(e)}")
    
    async def _process_image(self, file_path: Path, file_id: str, original_filename: str) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            # Chunk the text
            chunks = self._chunk_text(text) if text.strip() else []
            
            return {
                "id": file_id,
                "filename": original_filename,
                "type": "image",
                "text": text,
                "chunks": len(chunks),
                "chunk_data": chunks,
                "dimensions": image.size
            }
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")
    
    async def _process_audio(self, file_path: Path, file_id: str, original_filename: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        try:
            model = self._load_whisper()
            
            # Transcribe
            result = model.transcribe(str(file_path))
            text = result["text"]
            
            # Chunk the text
            chunks = self._chunk_text(text)
            
            return {
                "id": file_id,
                "filename": original_filename,
                "type": "audio",
                "text": text,
                "chunks": len(chunks),
                "chunk_data": chunks,
                "language": result.get("language"),
                "segments": len(result.get("segments", []))
            }
        except Exception as e:
            raise Exception(f"Error processing audio: {str(e)}")
    
    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks for embedding
        """
        if not text or not text.strip():
            return []
        
        # Create LlamaIndex document
        document = LlamaDocument(text=text)
        
        # Split into nodes
        nodes = self.sentence_splitter.get_nodes_from_documents([document])
        
        # Convert to dict format
        chunks = []
        for i, node in enumerate(nodes):
            chunks.append({
                "chunk_id": i,
                "text": node.get_content(),
                "start_idx": node.start_char_idx,
                "end_idx": node.end_char_idx
            })
        
        return chunks
