import io
from typing import List, Dict
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """Handles document parsing and text chunking"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process(self, content: bytes, filename: str) -> List[Dict[str, str]]:
        """
        Extract text from document and split into chunks
        
        Args:
            content: Raw file bytes
            filename: Name of the file
            
        Returns:
            List of chunks with metadata
        """
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = self._extract_from_pdf(content)
        elif filename.endswith('.txt'):
            text = content.decode('utf-8')
        elif filename.endswith('.docx'):
            text = self._extract_from_docx(content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Add metadata to each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return processed_chunks
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            # For DOCX support, install: pip install python-docx
            from docx import Document
            
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except ImportError:
            raise Exception("python-docx not installed. Run: pip install python-docx")
        except Exception as e:
            raise Exception(f"Error extracting DOCX text: {str(e)}")
    
    def get_statistics(self, chunks: List[Dict[str, str]]) -> Dict:
        """Get statistics about processed chunks"""
        total_chars = sum(len(chunk["text"]) for chunk in chunks)
        avg_chunk_size = total_chars / len(chunks) if chunks else 0
        
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": round(avg_chunk_size, 2)
        }