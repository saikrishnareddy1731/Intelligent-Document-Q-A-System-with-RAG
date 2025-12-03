import requests
import os
from typing import List, Dict

class QAEngine:
    """Handles question answering using Grok API with RAG"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.grok_api_key = os.getenv("GROK_API_KEY", "")
        if not self.grok_api_key:
            print("WARNING: GROK_API_KEY not found in environment!")
        else:
            print(f"✅ API Key loaded: {self.grok_api_key[:10]}...")
        
        self.grok_api_url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-beta"  # Check X.AI docs for latest model
    
    def generate_answer(self, question: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using retrieved context
        
        Args:
            question: User's question
            context_chunks: Relevant document chunks
            
        Returns:
            Generated answer
        """
        # Build context from chunks
        context = self._build_context(context_chunks)
        
        # Create prompt
        prompt = self._create_prompt(question, context)
        
        # Call Grok API
        try:
            answer = self._call_grok_api(prompt)
            return answer
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Combine chunks into context string"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "Unknown")
            text = chunk["text"]
            context_parts.append(f"[Source {i}: {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create RAG prompt"""
        prompt = f"""You are a helpful AI assistant that answers questions based on provided documents.

Context from documents:
{context}

Question: {question}

Instructions:
- Answer the question using ONLY the information from the provided context
- If the answer is not in the context, say "I don't have enough information to answer this question"
- Be concise and accurate
- Cite which source(s) you used if relevant

Answer:"""
        
        return prompt
    
    def _call_grok_api(self, prompt: str) -> str:
        """Make API call to Grok"""
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided document context."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temperature for more factual answers
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                self.grok_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                error_msg = f"Grok API error (status {response.status_code})"
                if response.text:
                    error_msg += f": {response.text}"
                return error_msg
        
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def generate_answer_streaming(self, question: str, context_chunks: List[Dict]):
        """
        Generate answer with streaming (for future enhancement)
        
        This would return a generator for streaming responses
        """
        # TODO: Implement streaming if Grok API supports it
        pass