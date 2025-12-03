import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [documents, setDocuments] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(false);

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadProgress(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert(`Document uploaded successfully! ${response.data.chunks_created} chunks created.`);
      fetchDocuments();
      event.target.value = ''; // Reset file input
    } catch (error) {
      alert('Error uploading document: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploadProgress(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      alert('Please enter a question');
      return;
    }

    setLoading(true);
    setAnswer(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        question: question,
        top_k: 3
      });

      setAnswer(response.data);
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/document/${docId}`);
      alert('Document deleted successfully');
      fetchDocuments();
      setAnswer(null); // Clear previous answers
    } catch (error) {
      alert('Error deleting document: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>📚 Intelligent Document Q&A System</h1>
        <p>Upload documents and ask questions using AI-powered RAG</p>
      </header>

      <div className="container">
        {/* Upload Section */}
        <div className="section upload-section">
          <h2>Upload Documents</h2>
          <div className="upload-box">
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleFileUpload}
              disabled={uploadProgress}
              id="file-input"
            />
            <label htmlFor="file-input" className="upload-label">
              {uploadProgress ? '⏳ Uploading...' : '📤 Choose File (PDF, TXT, DOCX)'}
            </label>
          </div>

          <div className="documents-list">
            <h3>Uploaded Documents ({documents.length})</h3>
            {documents.length === 0 ? (
              <p className="empty-state">No documents uploaded yet</p>
            ) : (
              <ul>
                {documents.map((doc) => (
                  <li key={doc.id} className="document-item">
                    <div>
                      <strong>{doc.filename}</strong>
                      <span className="doc-meta">
                        {doc.chunk_count} chunks · {new Date(doc.upload_date).toLocaleDateString()}
                      </span>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="delete-btn"
                    >
                      🗑️
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Q&A Section */}
        <div className="section qa-section">
          <h2>Ask Questions</h2>
          <div className="question-box">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your documents..."
              rows="4"
              disabled={loading || documents.length === 0}
            />
            <button
              onClick={handleAskQuestion}
              disabled={loading || documents.length === 0}
              className="ask-btn"
            >
              {loading ? '⏳ Thinking...' : '🔍 Ask Question'}
            </button>
          </div>

          {/* Answer Display */}
          {answer && (
            <div className="answer-box">
              <h3>Answer</h3>
              <p className="answer-text">{answer.answer}</p>
              
              <div className="metadata">
                <span>⚡ Response time: {answer.response_time}s</span>
              </div>

              <h4>Sources</h4>
              <div className="sources">
                {answer.sources.map((source, idx) => (
                  <div key={idx} className="source-item">
                    <strong>Source {idx + 1}:</strong> {source.metadata.source}
                    <p className="source-text">{source.text.substring(0, 200)}...</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {documents.length === 0 && (
            <p className="info-message">
              ℹ️ Please upload some documents first to ask questions
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;