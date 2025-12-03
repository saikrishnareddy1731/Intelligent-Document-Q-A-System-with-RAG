"""
Test script to verify the RAG system is working correctly
Run this after starting the backend server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50)

def test_root():
    print_header("Test 1: Check if server is running")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_upload_document():
    print_header("Test 2: Upload a sample document")
    
    # Create a sample text file
    sample_text = """
    Artificial Intelligence and Machine Learning
    
    Artificial Intelligence (AI) is the simulation of human intelligence by machines.
    Machine Learning (ML) is a subset of AI that enables systems to learn from data.
    
    Key concepts in ML include:
    - Supervised Learning: Learning from labeled data
    - Unsupervised Learning: Finding patterns in unlabeled data
    - Neural Networks: Computing systems inspired by biological neural networks
    - Deep Learning: Multi-layered neural networks for complex pattern recognition
    
    Applications of AI include natural language processing, computer vision,
    robotics, and recommendation systems.
    """
    
    files = {'file': ('test_document.txt', sample_text.encode(), 'text/plain')}
    
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files)
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json().get('document_id')
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_list_documents():
    print_header("Test 3: List all documents")
    try:
        response = requests.get(f"{BASE_URL}/documents")
        print(f"✅ Status: {response.status_code}")
        docs = response.json()
        print(f"Total documents: {len(docs)}")
        for doc in docs:
            print(f"  - {doc['filename']} ({doc['chunk_count']} chunks)")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_query(question):
    print_header(f"Test 4: Query - '{question}'")
    payload = {
        "question": question,
        "top_k": 3
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/query", json=payload)
        elapsed = time.time() - start_time
        
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        
        print(f"\n📝 Answer:")
        print(f"{result['answer']}")
        
        print(f"\n⚡ Response time: {result['response_time']}s (actual: {elapsed:.2f}s)")
        
        print(f"\n📚 Sources used:")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n  Source {i}: {source['metadata']['source']}")
            print(f"  Preview: {source['text'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False

def test_delete_document(doc_id):
    print_header("Test 5: Delete document")
    if not doc_id:
        print("⚠️  No document ID provided, skipping delete test")
        return False
    
    try:
        response = requests.delete(f"{BASE_URL}/document/{doc_id}")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("\n🚀 Starting RAG System Tests")
    print("Make sure the backend server is running on port 8000!\n")
    
    # Run tests
    doc_id = None
    
    if test_root():
        doc_id = test_upload_document()
        time.sleep(1)  # Give server time to process
        
        test_list_documents()
        time.sleep(1)
        
        # Test various questions
        questions = [
            "What is Machine Learning?",
            "What are the key concepts in ML?",
            "What are some applications of AI?"
        ]
        
        for question in questions:
            test_query(question)
            time.sleep(1)
        
        # Cleanup (optional)
        # test_delete_document(doc_id)
    
    print("\n" + "="*50)
    print("  Tests completed!")
    print("="*50)
    print("\n💡 Tips:")
    print("  - If tests fail, check backend logs")
    print("  - Ensure Grok API key is set in .env")
    print("  - Try with your own documents via the UI")

if __name__ == "__main__":
    main()