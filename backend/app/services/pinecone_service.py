"""
Pinecone vector database service for RAG functionality.

This service handles all interactions with Pinecone including:
- Index management
- Vector storage and retrieval
- Similarity search operations
- Embeddings management

    Mika Argyle - Aug 5 2025
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI
import numpy as np
from app.config import get_settings


class PineconeService:
    """
    Service for managing Pinecone vector operations.
    
    Handles vector storage, retrieval, and similarity search
    for the RAG chatbot functionality.
    """
    
    def __init__(self):
        """Initialize Pinecone service with configuration."""
        self.settings = get_settings()
        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index_name = self.settings.pinecone_index_name
        self.dimension = self.settings.embedding_dimension
        self.index = None
        
        # OpenAI client for embeddings
        self.openai_client = AsyncOpenAI(
            api_key=self.settings.openai_api_key
        )
    
    async def initialize_index(self) -> bool:
        """
        Initialize or create Pinecone index.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes.indexes]
            
            if self.index_name not in index_names:
                # Create new index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                print(f"✅ Created Pinecone index: {self.index_name}")
            else:
                print(f"✅ Using existing Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone index: {e}")
            return False
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text using OpenAI.
        
        Args:
            text (str): Text to embed
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            Exception: If embedding creation fails
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to create embedding: {e}")
    
    async def store_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Store multiple documents in Pinecone.
        
        Args:
            documents (List[Dict]): List of documents with 'id', 'text', and 'metadata'
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        if not self.index:
            await self.initialize_index()
        
        try:
            vectors_to_upsert = []
            
            for doc in documents:
                # Create embedding for document text
                embedding = await self.create_embedding(doc['text'])
                
                # Prepare vector for upsert
                vector = {
                    'id': doc['id'],
                    'values': embedding,
                    'metadata': {
                        'text': doc['text'],
                        **doc.get('metadata', {})
                    }
                }
                vectors_to_upsert.append(vector)
            
            # Batch upsert vectors
            self.index.upsert(vectors=vectors_to_upsert)
            print(f"✅ Stored {len(documents)} documents in Pinecone")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store documents: {e}")
            return False
    
    async def store_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Store a single document in Pinecone.
        
        Args:
            doc_id (str): Unique document identifier
            text (str): Document text content
            metadata (Dict): Additional metadata
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        document = {
            'id': doc_id,
            'text': text,
            'metadata': metadata or {}
        }
        return await self.store_documents([document])
    
    async def similarity_search(self, query: str, top_k: int = None, min_score: float = None) -> List[Dict[str, Any]]:
        """
        Perform similarity search for query text.
        
        Args:
            query (str): Query text
            top_k (int): Number of similar documents to retrieve
            min_score (float): Minimum similarity score threshold
            
        Returns:
            List[Dict]: List of similar documents with scores
        """
        if not self.index:
            await self.initialize_index()
        
        # Use configured defaults if not provided
        top_k = top_k or self.settings.rag_top_k
        min_score = min_score or self.settings.rag_min_score
        
        try:
            # Create embedding for query
            query_embedding = await self.create_embedding(query)
            
            # Search similar vectors
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Filter results by minimum score and format output
            similar_docs = []
            for match in search_results.matches:
                if match.score >= min_score:
                    similar_docs.append({
                        'id': match.id,
                        'score': match.score,
                        'text': match.metadata.get('text', ''),
                        'metadata': {k: v for k, v in match.metadata.items() if k != 'text'}
                    })
            
            print(f"✅ Found {len(similar_docs)} similar documents (score >= {min_score})")
            return similar_docs
            
        except Exception as e:
            print(f"❌ Similarity search failed: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from Pinecone.
        
        Args:
            doc_id (str): Document ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.index:
            await self.initialize_index()
        
        try:
            self.index.delete(ids=[doc_id])
            print(f"✅ Deleted document: {doc_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete document {doc_id}: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get Pinecone index statistics.
        
        Returns:
            Dict: Index statistics
        """
        if not self.index:
            await self.initialize_index()
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            print(f"❌ Failed to get index stats: {e}")
            return {}
    
    async def clear_index(self) -> bool:
        """
        Clear all vectors from the index.
        
        Returns:
            bool: True if clearing successful, False otherwise
        """
        if not self.index:
            await self.initialize_index()
        
        try:
            self.index.delete(delete_all=True)
            print("✅ Cleared all vectors from index")
            return True
        except Exception as e:
            print(f"❌ Failed to clear index: {e}")
            return False


# Singleton instance for easy importing
_pinecone_service = None

def get_pinecone_service() -> PineconeService:
    """
    Get singleton PineconeService instance.
    
    Returns:
        PineconeService: Singleton service instance
    """
    global _pinecone_service
    if _pinecone_service is None:
        _pinecone_service = PineconeService()
    return _pinecone_service