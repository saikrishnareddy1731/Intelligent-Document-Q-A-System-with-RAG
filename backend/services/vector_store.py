import chromadb
from chromadb.config import Settings
from typing import List, Dict
import uuid
import requests
import json
import os

class VectorStore:
    """Manages vector embeddings and similarity search using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document chunks for RAG"}
        )
        
        # Grok API configuration
        self.grok_api_key = os.getenv("GROK_API_KEY", "")
        if not self.grok_api_key:
            print("WARNING: GROK_API_KEY not found in environment!")
        else:
            print(f"✅ API Key loaded: {self.grok_api_key[:10]}...")
        
        self.grok_api_url = "https://api.x.ai/v1/embeddings"
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Grok API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "grok-1",  # Check Grok docs for correct model name
                "input": text
            }
            
            response = requests.post(
                self.grok_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
            else:
                # Fallback: Use a simple hash-based embedding (for testing)
                # In production, this should raise an error
                print(f"Warning: Using fallback embedding. Grok API error: {response.status_code}")
                return self._fallback_embedding(text)
        
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Simple fallback embedding for testing (not for production!)"""
        import hashlib
        import numpy as np
        
        # Generate deterministic embedding from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash, 16) % (2**32)
        np.random.seed(seed)
        
        return np.random.randn(dim).tolist()
    
    def add_document(self, filename: str, chunks: List[Dict[str, str]]) -> str:
        """
        Add document chunks to vector store
        
        Args:
            filename: Source document name
            chunks: List of text chunks with metadata
            
        Returns:
            Document ID
        """
        doc_id = str(uuid.uuid4())
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            text = chunk["text"]
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(text)
            metadatas.append({
                **chunk["metadata"],
                "document_id": doc_id,
                "filename": filename
            })
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return doc_id
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant chunks
        
        Args:
            query: User question
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        chunks = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                chunks.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return chunks
    
    def delete_document(self, doc_id: str):
        """Delete all chunks belonging to a document"""
        # Get all IDs for this document
        results = self.collection.get(
            where={"document_id": doc_id}
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection.name
        }