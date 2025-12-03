from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify API key is loaded
api_key = os.getenv("GROK_API_KEY", "")
if not api_key:
    print("❌ ERROR: GROK_API_KEY not found in .env file!")
else:
    print(f"✅ GROK_API_KEY loaded successfully: {api_key[:10]}...")

# Import custom services (we'll create these)
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore
from services.qa_engine import QAEngine

app = FastAPI(title="Document Q&A System with RAG")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
doc_processor = DocumentProcessor()
vector_store = VectorStore()
qa_engine = QAEngine()

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float

class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_date: str
    chunk_count: int

# In-memory storage (replace with database in production)
documents_db = {}

@app.get("/")
async def root():
    return {
        "message": "Document Q&A System API",
        "version": "1.0",
        "endpoints": ["/upload", "/query", "/documents"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(400, "Only PDF, TXT, and DOCX files supported")
        
        # Read file content
        content = await file.read()
        
        # Process document (extract text and split into chunks)
        chunks = doc_processor.process(content, file.filename)
        
        # Generate embeddings and store in vector DB
        doc_id = vector_store.add_document(file.filename, chunks)
        
        # Store metadata
        documents_db[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "upload_date": datetime.now().isoformat(),
            "chunk_count": len(chunks)
        }
        
        return {
            "message": "Document uploaded successfully",
            "document_id": doc_id,
            "chunks_created": len(chunks)
        }
    
    except Exception as e:
        raise HTTPException(500, f"Error processing document: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Ask a question about uploaded documents"""
    try:
        import time
        start_time = time.time()
        
        # Retrieve relevant chunks from vector store
        relevant_chunks = vector_store.search(request.question, top_k=request.top_k)
        
        if not relevant_chunks:
            raise HTTPException(404, "No relevant documents found")
        
        # Generate answer using Grok
        answer = qa_engine.generate_answer(request.question, relevant_chunks)
        
        response_time = time.time() - start_time
        
        return QueryResponse(
            answer=answer,
            sources=relevant_chunks,
            response_time=round(response_time, 2)
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error processing query: {str(e)}")

@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Get list of all uploaded documents"""
    return list(documents_db.values())

@app.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its embeddings"""
    try:
        if doc_id not in documents_db:
            raise HTTPException(404, "Document not found")
        
        # Remove from vector store
        vector_store.delete_document(doc_id)
        
        # Remove from metadata
        del documents_db[doc_id]
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        raise HTTPException(500, f"Error deleting document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)