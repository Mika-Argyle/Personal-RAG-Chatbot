"""
Tests for Pinecone service functionality.

Tests all Pinecone operations including vector storage, retrieval,
similarity search, and index management with proper mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.pinecone_service import PineconeService, get_pinecone_service


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for testing."""
    mock_index = MagicMock()
    mock_index.upsert = MagicMock(return_value=None)
    mock_index.query = MagicMock()
    mock_index.delete = MagicMock(return_value=None)
    mock_index.describe_index_stats = MagicMock()
    return mock_index


@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client for testing."""
    mock_client = MagicMock()
    
    # Mock index list
    mock_index_info = MagicMock()
    mock_index_info.name = "test-index"
    mock_client.list_indexes.return_value.indexes = [mock_index_info]
    
    mock_client.create_index = MagicMock(return_value=None)
    mock_client.Index = MagicMock()
    
    return mock_client


@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding response."""
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
    return mock_response


@pytest.fixture
def pinecone_service():
    """Create PineconeService instance for testing."""
    with patch('app.services.pinecone_service.Pinecone'), \
         patch('app.services.pinecone_service.AsyncOpenAI'):
        service = PineconeService()
        return service


class TestPineconeServiceInitialization:
    """Test PineconeService initialization and setup."""

    @pytest.mark.unit
    def test_service_initialization(self, pinecone_service):
        """Test PineconeService initializes correctly."""
        assert pinecone_service.settings is not None
        assert pinecone_service.index_name == "portfolio-rag"
        assert pinecone_service.dimension == 1536
        assert pinecone_service.index is None  # Not initialized yet

    @pytest.mark.unit 
    @patch('app.services.pinecone_service.Pinecone')
    @patch('app.services.pinecone_service.AsyncOpenAI')
    async def test_initialize_index_new_index(self, mock_openai, mock_pinecone):
        """Test initializing a new Pinecone index."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.list_indexes.return_value.indexes = []  # No existing indexes
        mock_client.create_index = MagicMock()
        mock_client.Index = MagicMock()
        mock_pinecone.return_value = mock_client
        
        service = PineconeService()
        result = await service.initialize_index()
        
        assert result is True
        mock_client.create_index.assert_called_once()
        mock_client.Index.assert_called_once_with("portfolio-rag")

    @pytest.mark.unit
    @patch('app.services.pinecone_service.Pinecone')
    @patch('app.services.pinecone_service.AsyncOpenAI')
    async def test_initialize_index_existing_index(self, mock_openai, mock_pinecone):
        """Test initializing with existing Pinecone index."""
        # Setup mocks
        mock_client = MagicMock()
        mock_index_info = MagicMock()
        mock_index_info.name = "portfolio-rag"
        mock_client.list_indexes.return_value.indexes = [mock_index_info]
        mock_client.create_index = MagicMock()
        mock_client.Index = MagicMock()
        mock_pinecone.return_value = mock_client
        
        service = PineconeService()
        result = await service.initialize_index()
        
        assert result is True
        mock_client.create_index.assert_not_called()  # Should not create new index
        mock_client.Index.assert_called_once_with("portfolio-rag")

    @pytest.mark.unit
    @patch('app.services.pinecone_service.Pinecone')
    @patch('app.services.pinecone_service.AsyncOpenAI')
    async def test_initialize_index_failure(self, mock_openai, mock_pinecone):
        """Test initialize_index handles failures gracefully."""
        # Setup mocks to raise exception
        mock_client = MagicMock()
        mock_client.list_indexes.side_effect = Exception("Connection failed")
        mock_pinecone.return_value = mock_client
        
        service = PineconeService()
        result = await service.initialize_index()
        
        assert result is False


class TestEmbeddingOperations:
    """Test embedding creation and operations."""

    @pytest.mark.unit
    async def test_create_embedding_success(self, pinecone_service, mock_openai_embedding):
        """Test successful embedding creation."""
        with patch.object(pinecone_service.openai_client.embeddings, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_embedding
            
            result = await pinecone_service.create_embedding("test text")
            
            assert len(result) == 1536
            assert result == [0.1, 0.2, 0.3] * 512
            mock_create.assert_called_once_with(
                model="text-embedding-3-small",
                input="test text"
            )

    @pytest.mark.unit
    async def test_create_embedding_failure(self, pinecone_service):
        """Test embedding creation handles failures."""
        with patch.object(pinecone_service.openai_client.embeddings, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("OpenAI API Error")
            
            with pytest.raises(Exception, match="Failed to create embedding"):
                await pinecone_service.create_embedding("test text")


class TestDocumentStorage:
    """Test document storage operations."""

    @pytest.mark.unit
    async def test_store_single_document_success(self, pinecone_service, mock_openai_embedding):
        """Test storing a single document successfully."""
        # Mock index initialization and embedding
        pinecone_service.index = MagicMock()
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            result = await pinecone_service.store_document(
                doc_id="test-doc-1",
                text="This is a test document",
                metadata={"source": "test"}
            )
            
            assert result is True
            mock_embed.assert_called_once_with("This is a test document")
            pinecone_service.index.upsert.assert_called_once()

    @pytest.mark.unit
    async def test_store_multiple_documents_success(self, pinecone_service):
        """Test storing multiple documents successfully."""
        # Mock index and embedding
        pinecone_service.index = MagicMock()
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            documents = [
                {"id": "doc1", "text": "Document 1", "metadata": {"type": "test"}},
                {"id": "doc2", "text": "Document 2", "metadata": {"type": "test"}}
            ]
            
            result = await pinecone_service.store_documents(documents)
            
            assert result is True
            assert mock_embed.call_count == 2
            pinecone_service.index.upsert.assert_called_once()

    @pytest.mark.unit
    async def test_store_documents_failure(self, pinecone_service):
        """Test store_documents handles failures gracefully."""
        pinecone_service.index = MagicMock()
        pinecone_service.index.upsert.side_effect = Exception("Pinecone error")
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            documents = [{"id": "doc1", "text": "Document 1"}]
            result = await pinecone_service.store_documents(documents)
            
            assert result is False


class TestSimilaritySearch:
    """Test similarity search operations."""

    @pytest.mark.unit
    async def test_similarity_search_success(self, pinecone_service):
        """Test successful similarity search."""
        # Mock index and search results
        pinecone_service.index = MagicMock()
        
        # Mock search results
        mock_match1 = MagicMock()
        mock_match1.id = "doc1"
        mock_match1.score = 0.85
        mock_match1.metadata = {"text": "Similar document 1", "source": "test"}
        
        mock_match2 = MagicMock()
        mock_match2.id = "doc2"
        mock_match2.score = 0.75
        mock_match2.metadata = {"text": "Similar document 2", "source": "test"}
        
        mock_results = MagicMock()
        mock_results.matches = [mock_match1, mock_match2]
        pinecone_service.index.query.return_value = mock_results
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            results = await pinecone_service.similarity_search("test query")
            
            assert len(results) == 2
            assert results[0]["id"] == "doc1"
            assert results[0]["score"] == 0.85
            assert results[0]["text"] == "Similar document 1"
            assert results[1]["id"] == "doc2"
            assert results[1]["score"] == 0.75

    @pytest.mark.unit
    async def test_similarity_search_with_score_filter(self, pinecone_service):
        """Test similarity search with minimum score filtering."""
        pinecone_service.index = MagicMock()
        
        # Mock search results with different scores
        mock_match1 = MagicMock()
        mock_match1.id = "doc1"
        mock_match1.score = 0.85  # Above threshold
        mock_match1.metadata = {"text": "High similarity document"}
        
        mock_match2 = MagicMock()
        mock_match2.id = "doc2"
        mock_match2.score = 0.65  # Below threshold
        mock_match2.metadata = {"text": "Low similarity document"}
        
        mock_results = MagicMock()
        mock_results.matches = [mock_match1, mock_match2]
        pinecone_service.index.query.return_value = mock_results
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            results = await pinecone_service.similarity_search(
                "test query", 
                min_score=0.7
            )
            
            # Should only return documents with score >= 0.7
            assert len(results) == 1
            assert results[0]["id"] == "doc1"
            assert results[0]["score"] == 0.85

    @pytest.mark.unit
    async def test_similarity_search_failure(self, pinecone_service):
        """Test similarity search handles failures gracefully."""
        pinecone_service.index = MagicMock()
        pinecone_service.index.query.side_effect = Exception("Search failed")
        
        with patch.object(pinecone_service, 'create_embedding',
                         new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 512
            
            results = await pinecone_service.similarity_search("test query")
            
            assert results == []


class TestIndexManagement:
    """Test index management operations."""

    @pytest.mark.unit
    async def test_delete_document_success(self, pinecone_service):
        """Test successful document deletion."""
        pinecone_service.index = MagicMock()
        
        result = await pinecone_service.delete_document("test-doc-1")
        
        assert result is True
        pinecone_service.index.delete.assert_called_once_with(ids=["test-doc-1"])

    @pytest.mark.unit
    async def test_delete_document_failure(self, pinecone_service):
        """Test delete_document handles failures gracefully."""
        pinecone_service.index = MagicMock()
        pinecone_service.index.delete.side_effect = Exception("Delete failed")
        
        result = await pinecone_service.delete_document("test-doc-1")
        
        assert result is False

    @pytest.mark.unit
    async def test_get_index_stats_success(self, pinecone_service):
        """Test getting index statistics successfully."""
        pinecone_service.index = MagicMock()
        
        # Mock stats response
        mock_stats = MagicMock()
        mock_stats.total_vector_count = 100
        mock_stats.dimension = 1536
        mock_stats.index_fullness = 0.1
        mock_stats.namespaces = {"default": MagicMock()}
        pinecone_service.index.describe_index_stats.return_value = mock_stats
        
        stats = await pinecone_service.get_index_stats()
        
        assert stats["total_vectors"] == 100
        assert stats["dimension"] == 1536
        assert stats["index_fullness"] == 0.1
        assert "namespaces" in stats

    @pytest.mark.unit
    async def test_get_index_stats_failure(self, pinecone_service):
        """Test get_index_stats handles failures gracefully."""
        pinecone_service.index = MagicMock()
        pinecone_service.index.describe_index_stats.side_effect = Exception("Stats failed")
        
        stats = await pinecone_service.get_index_stats()
        
        assert stats == {}

    @pytest.mark.unit
    async def test_clear_index_success(self, pinecone_service):
        """Test clearing index successfully."""
        pinecone_service.index = MagicMock()
        
        result = await pinecone_service.clear_index()
        
        assert result is True
        pinecone_service.index.delete.assert_called_once_with(delete_all=True)

    @pytest.mark.unit
    async def test_clear_index_failure(self, pinecone_service):
        """Test clear_index handles failures gracefully."""
        pinecone_service.index = MagicMock()
        pinecone_service.index.delete.side_effect = Exception("Clear failed")
        
        result = await pinecone_service.clear_index()
        
        assert result is False


class TestSingletonPattern:
    """Test singleton pattern for service instance."""

    @pytest.mark.unit
    def test_get_pinecone_service_singleton(self):
        """Test that get_pinecone_service returns the same instance."""
        with patch('app.services.pinecone_service.Pinecone'), \
             patch('app.services.pinecone_service.AsyncOpenAI'):
            
            service1 = get_pinecone_service()
            service2 = get_pinecone_service()
            
            assert service1 is service2


class TestConfigurationIntegration:
    """Test integration with configuration settings."""

    @pytest.mark.unit
    @patch('app.services.pinecone_service.get_settings')
    @patch('app.services.pinecone_service.Pinecone')
    @patch('app.services.pinecone_service.AsyncOpenAI')
    def test_service_uses_correct_settings(self, mock_openai, mock_pinecone, mock_settings):
        """Test that service uses configuration settings correctly."""
        # Mock settings
        mock_config = MagicMock()
        mock_config.pinecone_api_key = "test-key"
        mock_config.pinecone_index_name = "test-index"
        mock_config.embedding_dimension = 1536
        mock_config.openai_api_key = "test-openai-key"
        mock_config.rag_top_k = 10
        mock_config.rag_min_score = 0.8
        mock_settings.return_value = mock_config
        
        service = PineconeService()
        
        assert service.index_name == "test-index"
        assert service.dimension == 1536
        mock_pinecone.assert_called_once_with(api_key="test-key")
        mock_openai.assert_called_once_with(api_key="test-openai-key")