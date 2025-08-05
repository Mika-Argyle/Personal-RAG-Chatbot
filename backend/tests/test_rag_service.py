"""
Tests for RAG (Retrieval-Augmented Generation) service functionality.

Tests RAG operations including document addition, context retrieval,
response generation, and integration between Pinecone and OpenAI.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rag_service import RAGService, get_rag_service


@pytest.fixture
def mock_pinecone_service():
    """Mock Pinecone service for testing."""
    mock_service = MagicMock()
    mock_service.initialize_index = AsyncMock(return_value=True)
    mock_service.store_documents = AsyncMock(return_value=True)
    mock_service.similarity_search = AsyncMock(return_value=[])
    mock_service.get_index_stats = AsyncMock(return_value={
        "total_vectors": 100,
        "dimension": 1536,
        "index_fullness": 0.1
    })
    mock_service.clear_index = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test RAG response based on the provided context."
    return mock_response


@pytest.fixture
def rag_service():
    """Create RAGService instance for testing."""
    with patch('app.services.rag_service.get_pinecone_service'), \
         patch('app.services.rag_service.AsyncOpenAI'):
        service = RAGService()
        return service


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "text": "This is a test document about machine learning and AI projects.",
            "metadata": {"source": "portfolio", "type": "project"}
        },
        {
            "id": "doc2", 
            "text": "Information about web development skills including React, Python, and FastAPI.",
            "metadata": {"source": "resume", "type": "skills"}
        }
    ]


@pytest.fixture
def sample_search_results():
    """Sample Pinecone search results."""
    return [
        {
            "id": "doc1_chunk_0",
            "score": 0.85,
            "text": "This is a test document about machine learning and AI projects.",
            "metadata": {"source": "portfolio", "parent_doc_id": "doc1"}
        },
        {
            "id": "doc2_chunk_0",
            "score": 0.75,
            "text": "Information about web development skills including React, Python, and FastAPI.",
            "metadata": {"source": "resume", "parent_doc_id": "doc2"}
        }
    ]


class TestRAGServiceInitialization:
    """Test RAG service initialization."""

    @pytest.mark.unit
    def test_service_initialization(self, rag_service):
        """Test RAGService initializes correctly."""
        assert rag_service.settings is not None
        assert rag_service.pinecone_service is not None
        assert rag_service.openai_client is not None

    @pytest.mark.unit
    async def test_initialize_success(self, rag_service, mock_pinecone_service):
        """Test successful RAG service initialization."""
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.initialize()
        
        assert result is True
        mock_pinecone_service.initialize_index.assert_called_once()

    @pytest.mark.unit
    async def test_initialize_failure(self, rag_service, mock_pinecone_service):
        """Test RAG service initialization handles failures."""
        mock_pinecone_service.initialize_index.return_value = False
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.initialize()
        
        assert result is False


class TestDocumentManagement:
    """Test document addition and management."""

    @pytest.mark.unit
    async def test_add_documents_success(self, rag_service, mock_pinecone_service, sample_documents):
        """Test successfully adding documents to knowledge base."""
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.add_documents(sample_documents)
        
        assert result is True
        mock_pinecone_service.store_documents.assert_called_once()
        
        # Check that documents were chunked
        call_args = mock_pinecone_service.store_documents.call_args[0][0]
        assert len(call_args) >= len(sample_documents)  # Should have at least as many chunks

    @pytest.mark.unit
    async def test_add_documents_failure(self, rag_service, mock_pinecone_service, sample_documents):
        """Test add_documents handles failures gracefully."""
        mock_pinecone_service.store_documents.return_value = False
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.add_documents(sample_documents)
        
        assert result is False

    @pytest.mark.unit
    def test_chunk_document(self, rag_service):
        """Test document chunking functionality."""
        long_text = "This is a test document. " * 100  # Create long text
        
        chunks = rag_service._chunk_document(long_text, "test_doc", {"source": "test"})
        
        assert len(chunks) > 1  # Should create multiple chunks
        
        # Check chunk structure
        for i, chunk in enumerate(chunks):
            assert chunk["id"] == f"test_doc_chunk_{i}"
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["parent_doc_id"] == "test_doc"
            assert chunk["metadata"]["chunk_number"] == i

    @pytest.mark.unit
    def test_chunk_document_short_text(self, rag_service):
        """Test chunking with text shorter than chunk size."""
        short_text = "This is a short document."
        
        chunks = rag_service._chunk_document(short_text, "test_doc", {"source": "test"})
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == short_text
        assert chunks[0]["id"] == "test_doc_chunk_0"


class TestRAGChat:
    """Test RAG chat functionality."""

    @pytest.mark.unit
    async def test_chat_with_context_success(self, rag_service, mock_pinecone_service, 
                                           mock_openai_response, sample_search_results):
        """Test successful RAG chat with context."""
        # Setup mocks
        rag_service.pinecone_service = mock_pinecone_service
        mock_pinecone_service.similarity_search.return_value = sample_search_results
        
        with patch.object(rag_service.openai_client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            result = await rag_service.chat_with_context("Tell me about machine learning projects")
            
            assert "response" in result
            assert result["response"] == "This is a test RAG response based on the provided context."
            assert result["sources_used"] == 2
            assert len(result["sources"]) == 2
            assert result["model_used"] == "gpt-4o-mini"
            
            # Verify OpenAI was called with context
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            
            # Should have system message with context and user message
            assert len(messages) >= 2
            assert messages[0]["role"] == "system"
            assert "Context 1" in messages[0]["content"]
            assert messages[-1]["role"] == "user"

    @pytest.mark.unit
    async def test_chat_with_context_no_results(self, rag_service, mock_pinecone_service, 
                                              mock_openai_response):
        """Test RAG chat when no relevant documents found."""
        # Setup mocks - no search results
        rag_service.pinecone_service = mock_pinecone_service
        mock_pinecone_service.similarity_search.return_value = []
        
        with patch.object(rag_service.openai_client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            result = await rag_service.chat_with_context("Tell me about something random")
            
            assert result["sources_used"] == 0
            assert len(result["sources"]) == 0
            
            # Should still call OpenAI with "No relevant context found"
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            assert "No relevant context found" in messages[0]["content"]

    @pytest.mark.unit
    async def test_chat_with_context_with_history(self, rag_service, mock_pinecone_service, 
                                                mock_openai_response):
        """Test RAG chat with chat history."""
        rag_service.pinecone_service = mock_pinecone_service
        mock_pinecone_service.similarity_search.return_value = []
        
        chat_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        with patch.object(rag_service.openai_client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            await rag_service.chat_with_context("Follow up question", chat_history)
            
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            
            # Should include system message, history, and current message
            assert len(messages) >= 4
            assert messages[0]["role"] == "system"
            assert messages[1]["content"] == "Previous question"
            assert messages[2]["content"] == "Previous answer"
            assert messages[-1]["content"] == "Follow up question"

    @pytest.mark.unit
    async def test_chat_with_context_failure(self, rag_service, mock_pinecone_service):
        """Test RAG chat handles failures gracefully."""
        rag_service.pinecone_service = mock_pinecone_service
        mock_pinecone_service.similarity_search.side_effect = Exception("Search failed")
        
        result = await rag_service.chat_with_context("Test question")
        
        assert "error" in result
        assert "RAG chat failed" in result["error"]
        assert "I apologize" in result["response"]
        assert result["sources_used"] == 0

    @pytest.mark.unit
    def test_prepare_context(self, rag_service, sample_search_results):
        """Test context preparation from search results."""
        context = rag_service._prepare_context(sample_search_results)
        
        assert "Context 1 (relevance: 0.85)" in context
        assert "Context 2 (relevance: 0.75)" in context
        assert "machine learning and AI projects" in context
        assert "web development skills" in context

    @pytest.mark.unit
    def test_prepare_context_empty(self, rag_service):
        """Test context preparation with no results."""
        context = rag_service._prepare_context([])
        
        assert context == "No relevant context found."

    @pytest.mark.unit
    def test_prepare_messages(self, rag_service):
        """Test message preparation for OpenAI."""
        context = "Test context information"
        user_message = "Test question"
        
        messages = rag_service._prepare_messages(user_message, context)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert context in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user_message

    @pytest.mark.unit
    def test_prepare_messages_with_history(self, rag_service):
        """Test message preparation with chat history."""
        context = "Test context"
        user_message = "Test question"
        history = [
            {"role": "user", "content": "Previous Q"},
            {"role": "assistant", "content": "Previous A"}
        ]
        
        messages = rag_service._prepare_messages(user_message, context, history)
        
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Previous Q"
        assert messages[2]["content"] == "Previous A"
        assert messages[3]["content"] == user_message


class TestKnowledgeBaseManagement:
    """Test knowledge base management operations."""

    @pytest.mark.unit
    async def test_get_knowledge_base_stats(self, rag_service, mock_pinecone_service):
        """Test getting knowledge base statistics."""
        rag_service.pinecone_service = mock_pinecone_service
        
        stats = await rag_service.get_knowledge_base_stats()
        
        assert stats["total_documents"] == 100
        assert stats["index_dimension"] == 1536
        assert stats["index_fullness"] == 0.1
        assert stats["embedding_model"] == "text-embedding-3-small"
        assert stats["chat_model"] == "gpt-4o-mini"
        assert "rag_settings" in stats

    @pytest.mark.unit
    async def test_get_knowledge_base_stats_failure(self, rag_service, mock_pinecone_service):
        """Test get_knowledge_base_stats handles failures."""
        mock_pinecone_service.get_index_stats.side_effect = Exception("Stats failed")
        rag_service.pinecone_service = mock_pinecone_service
        
        stats = await rag_service.get_knowledge_base_stats()
        
        assert "error" in stats

    @pytest.mark.unit
    async def test_clear_knowledge_base_success(self, rag_service, mock_pinecone_service):
        """Test successfully clearing knowledge base."""
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.clear_knowledge_base()
        
        assert result is True
        mock_pinecone_service.clear_index.assert_called_once()

    @pytest.mark.unit
    async def test_clear_knowledge_base_failure(self, rag_service, mock_pinecone_service):
        """Test clear_knowledge_base handles failures."""
        mock_pinecone_service.clear_index.return_value = False
        rag_service.pinecone_service = mock_pinecone_service
        
        result = await rag_service.clear_knowledge_base()
        
        assert result is False


class TestSingletonPattern:
    """Test singleton pattern for RAG service."""

    @pytest.mark.unit
    def test_get_rag_service_singleton(self):
        """Test that get_rag_service returns the same instance."""
        with patch('app.services.rag_service.get_pinecone_service'), \
             patch('app.services.rag_service.AsyncOpenAI'):
            
            service1 = get_rag_service()
            service2 = get_rag_service()
            
            assert service1 is service2


class TestConfigurationIntegration:
    """Test integration with configuration settings."""

    @pytest.mark.unit
    @patch('app.services.rag_service.get_settings')
    @patch('app.services.rag_service.get_pinecone_service')
    @patch('app.services.rag_service.AsyncOpenAI')
    def test_service_uses_correct_settings(self, mock_openai, mock_pinecone, mock_settings):
        """Test that RAG service uses configuration settings correctly."""
        # Mock settings
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-openai-key"
        mock_config.openai_model = "gpt-4o-mini"
        mock_config.rag_top_k = 5
        mock_config.rag_min_score = 0.7
        mock_config.chunk_size = 1000
        mock_config.chunk_overlap = 200
        mock_settings.return_value = mock_config
        
        service = RAGService()
        
        mock_openai.assert_called_once_with(api_key="test-openai-key")
        assert service.settings.rag_top_k == 5
        assert service.settings.rag_min_score == 0.7