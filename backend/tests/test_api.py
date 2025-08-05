"""
Tests for FastAPI endpoints and API functionality.

Tests all API endpoints, request/response models, error handling,
and middleware configuration.
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


class TestChatEndpoint:
    """Test the chat endpoint (/api/chat)."""

    @pytest.mark.unit
    def test_chat_endpoint_success(self, client, mock_openai_response):
        """Test successful chat request."""
        with patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            response = client.post(
                "/api/chat",
                json={"message": "Hello, how are you?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "response" in data
            assert "model_used" in data
            assert data["response"] == "Test response from AI assistant"
            assert data["model_used"] == "gpt-4o-mini"

    @pytest.mark.unit
    def test_chat_endpoint_openai_call_parameters(self, client, 
                                                  mock_openai_response):
        """Test that OpenAI is called with correct parameters."""
        with patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            test_message = "What is Python?"
            client.post("/api/chat", json={"message": test_message})
            
            # Verify OpenAI was called with correct parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            
            assert call_args.kwargs["model"] == "gpt-4o-mini"
            assert call_args.kwargs["max_tokens"] == 500
            assert call_args.kwargs["temperature"] == 0.7
            
            # Check messages structure
            messages = call_args.kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == test_message

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
    def test_chat_endpoint_openai_error(self, client):
        """Test chat endpoint when OpenAI API fails."""
        with patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("OpenAI API Error")
            
            response = client.post(
                "/api/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200  # App handles errors gracefully
            data = response.json()
            
            assert "error" in data
            assert "Chat failed" in data["error"]

    @pytest.mark.unit
    def test_chat_endpoint_system_message(self, client, mock_openai_response):
        """Test that system message is properly configured."""
        with patch('app.main.openai_client.chat.completions.create', 
                   new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            client.post("/api/chat", json={"message": "Test"})
            
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            system_message = messages[0]
            
            assert system_message["role"] == "system"
            expected_content = ("You are a helpful assistant for a "
                              "software developer's portfolio website.")
            assert system_message["content"] == expected_content


class TestRequestResponseModels:
    """Test Pydantic request/response models."""

    @pytest.mark.unit
    def test_chat_request_model_valid(self, client):
        """Test ChatRequest model accepts valid data."""
        valid_requests = [
            {"message": "Hello"},
            {"message": "What is machine learning?"},
            {"message": "Tell me about your projects"},
        ]
        
        for request_data in valid_requests:
            response = client.post("/api/chat", json=request_data)
            # Should not return validation error (422)
            assert response.status_code != 422

    @pytest.mark.unit
    def test_chat_request_model_invalid(self, client):
        """Test ChatRequest model rejects invalid data."""
        invalid_requests = [
            {},  # Missing message field
            {"msg": "Hello"},  # Wrong field name
            {"message": 123},  # Wrong data type
            {"message": None},  # Null value
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


