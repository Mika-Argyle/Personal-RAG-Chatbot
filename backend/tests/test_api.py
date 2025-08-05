"""
Tests for FastAPI endpoints and API functionality.

Tests all API endpoints, request/response models, error handling,
and middleware configuration with RAG integration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response from AI assistant"
    return mock_response


@pytest.fixture
def mock_rag_response():
    """Mock RAG service response."""
    return {
        "response": "Test RAG response with context",
        "model_used": "gpt-4o-mini",
        "sources_used": 2,
        "sources": [
            {"id": "doc1", "score": 0.85, "metadata": {"type": "resume"}},
            {"id": "doc2", "score": 0.75, "metadata": {"type": "project"}}
        ]
    }


@pytest.fixture
def mock_knowledge_base_stats():
    """Mock knowledge base statistics."""
    return {
        "total_documents": 25,
        "index_dimension": 1536,
        "index_fullness": 0.1,
        "embedding_model": "text-embedding-3-small",
        "chat_model": "gpt-4o-mini",
        "rag_settings": {
            "top_k": 5,
            "min_score": 0.7,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    }


class TestRootEndpoint:
    """Test the root endpoint (/)."""

    @pytest.mark.unit
    def test_root_endpoint_success(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Personal RAG Chatbot API is running!"
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    @pytest.mark.unit
    def test_root_endpoint_response_structure(self, client):
        """Test root endpoint returns expected structure."""
        response = client.get("/")
        data = response.json()
        
        # Check all required keys are present
        required_keys = ["message", "status", "version"]
        for key in required_keys:
            assert key in data
        
        # Check data types
        assert isinstance(data["message"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    @pytest.mark.unit
    def test_health_endpoint_success(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"

    @pytest.mark.unit
    def test_health_endpoint_response_structure(self, client):
        """Test health endpoint returns expected structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert isinstance(data["status"], str)


class TestRAGChatEndpoint:
    """Test the RAG-enabled chat endpoint (/api/chat)."""

    @pytest.mark.unit
    def test_chat_endpoint_rag_success(self, client, mock_rag_response):
        """Test successful RAG chat request."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = mock_rag_response
            
            response = client.post(
                "/api/chat",
                json={"message": "Tell me about your experience"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check new RAG response structure
            assert "response" in data
            assert "model_used" in data
            assert "sources_used" in data
            assert "sources" in data
            
            assert data["response"] == "Test RAG response with context"
            assert data["model_used"] == "gpt-4o-mini"
            assert data["sources_used"] == 2
            assert len(data["sources"]) == 2

    @pytest.mark.unit
    def test_chat_endpoint_with_chat_history(self, client, mock_rag_response):
        """Test chat request with chat history."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = mock_rag_response
            
            chat_history = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"}
            ]
            
            response = client.post(
                "/api/chat",
                json={
                    "message": "Follow up question", 
                    "chat_history": chat_history
                }
            )
            
            assert response.status_code == 200
            
            # Verify RAG service was called with history
            mock_rag.assert_called_once_with(
                user_message="Follow up question",
                chat_history=chat_history
            )

    @pytest.mark.unit
    def test_chat_endpoint_fallback_to_openai(self, client, mock_openai_response):
        """Test fallback to OpenAI when RAG service fails."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag, \
             patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_openai:
            
            # Make RAG service fail
            mock_rag.side_effect = Exception("RAG service error")
            mock_openai.return_value = mock_openai_response
            
            response = client.post(
                "/api/chat",
                json={"message": "Test fallback"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should use fallback response
            assert data["response"] == "Test response from AI assistant" 
            assert data["sources_used"] == 0
            assert data["sources"] == []
            
            # Verify fallback was used
            mock_openai.assert_called_once()

    @pytest.mark.unit
    def test_chat_endpoint_rag_parameters(self, client, mock_rag_response):
        """Test that RAG service is called with correct parameters."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = mock_rag_response
            
            test_message = "What are your skills?"
            client.post("/api/chat", json={"message": test_message})
            
            # Verify RAG service was called with correct parameters
            mock_rag.assert_called_once_with(
                user_message=test_message,
                chat_history=[]  # Empty list when no history provided
            )

    @pytest.mark.unit
    def test_chat_endpoint_invalid_request_missing_message(self, client):
        """Test chat endpoint with missing message field."""
        response = client.post("/api/chat", json={})
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_chat_endpoint_invalid_request_empty_message(self, client):
        """Test chat endpoint with empty message."""
        response = client.post("/api/chat", json={"message": ""})
        
        # Should still process empty messages (let OpenAI handle it)
        # But might want to add validation later
        assert response.status_code in [200, 422]

    @pytest.mark.unit
    def test_chat_endpoint_invalid_json(self, client):
        """Test chat endpoint with invalid JSON."""
        response = client.post(
            "/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    @pytest.mark.unit
    def test_chat_endpoint_rag_service_error(self, client, mock_openai_response):
        """Test chat endpoint when RAG service has an error but returns error response."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag, \
             patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_openai:
            
            # Make RAG return error response (simulating handled errors)
            mock_rag.return_value = {
                "error": "RAG processing failed: vector search error",
                "response": "I apologize, but I'm having trouble accessing my knowledge base right now. Please try again.",
                "model_used": "gpt-4o-mini",
                "sources_used": 0,
                "sources": []
            }
            
            response = client.post(
                "/api/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should get the error response from RAG service
            assert "I apologize" in data["response"]
            assert data["sources_used"] == 0

    @pytest.mark.unit
    def test_chat_endpoint_complete_failure(self, client):
        """Test chat endpoint when both RAG and fallback fail."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag, \
             patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_openai:
            
            # Make both services fail
            mock_rag.side_effect = Exception("RAG failed")
            mock_openai.side_effect = Exception("OpenAI failed")
            
            response = client.post(
                "/api/chat",
                json={"message": "Test complete failure"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return graceful error response as ChatResponse
            assert "I apologize" in data["response"]
            assert "technical difficulties" in data["response"] 
            assert data["model_used"] == "error"
            assert data["sources_used"] == 0
            assert data["sources"] == []


class TestKnowledgeBaseStatsEndpoint:
    """Test the knowledge base stats endpoint."""

    @pytest.mark.unit
    def test_knowledge_base_stats_success(self, client, mock_knowledge_base_stats):
        """Test successful knowledge base stats request."""
        with patch('app.main.rag_service.get_knowledge_base_stats', 
                   new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = mock_knowledge_base_stats
            
            response = client.get("/api/knowledge-base/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check stats structure
            assert data["total_documents"] == 25
            assert data["index_dimension"] == 1536
            assert data["embedding_model"] == "text-embedding-3-small"
            assert data["chat_model"] == "gpt-4o-mini"
            assert "rag_settings" in data

    @pytest.mark.unit  
    def test_knowledge_base_stats_failure(self, client):
        """Test knowledge base stats endpoint handles failures."""
        with patch('app.main.rag_service.get_knowledge_base_stats', 
                   new_callable=AsyncMock) as mock_stats:
            mock_stats.side_effect = Exception("Stats service failed")
            
            response = client.get("/api/knowledge-base/stats")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to get knowledge base stats" in data["detail"]


class TestRequestResponseModels:
    """Test Pydantic request/response models."""

    @pytest.mark.unit
    def test_chat_request_model_valid(self, client, mock_rag_response):
        """Test ChatRequest model accepts valid data including chat history."""
        with patch('app.main.rag_service.chat_with_context', 
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = mock_rag_response
            
            valid_requests = [
                {"message": "Hello"},
                {"message": "Hello", "chat_history": []},
                {"message": "Hello", "chat_history": [
                    {"role": "user", "content": "Previous question"}
                ]},
            ]
            
            for request_data in valid_requests:
                response = client.post("/api/chat", json=request_data)
                # Should not return validation error (422)
                assert response.status_code == 200

    @pytest.mark.unit
    def test_chat_request_model_invalid(self, client):
        """Test ChatRequest model rejects invalid data."""
        invalid_requests = [
            {},  # Missing message field
            {"msg": "Hello"},  # Wrong field name
            {"message": 123},  # Wrong data type
            {"message": None},  # Null value
            {"message": "Hello", "chat_history": "invalid"},  # Wrong history type
        ]
        
        for request_data in invalid_requests:
            response = client.post("/api/chat", json=request_data)
            assert response.status_code == 422


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    @pytest.mark.unit
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in cross-origin responses."""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.unit
    def test_preflight_request(self, client):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should handle preflight requests
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    def test_nonexistent_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_wrong_http_method(self, client):
        """Test using wrong HTTP method on endpoints."""
        # POST to GET endpoint
        response = client.post("/health")
        assert response.status_code == 405  # Method not allowed
        
        # GET to POST endpoint
        response = client.get("/api/chat")
        assert response.status_code == 405

    @pytest.mark.integration
    def test_large_message_handling(self, client, mock_openai_response):
        """Test handling of very large messages."""
        with patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            # Create a large message (10KB)
            large_message = "A" * 10000
            
            response = client.post(
                "/api/chat",
                json={"message": large_message}
            )
            
            # Should handle large messages gracefully
            assert response.status_code == 200


