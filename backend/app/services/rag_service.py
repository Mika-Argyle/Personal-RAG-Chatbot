"""
RAG (Retrieval-Augmented Generation) service for the Personal RAG Chatbot.

This service combines Pinecone vector search with OpenAI's chat completions
to provide contextually-aware responses based on stored documents.

    Mika Argyle - Aug 5 2025
"""

from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import get_settings
from app.services.pinecone_service import get_pinecone_service


class RAGService:
    """
    Service for Retrieval-Augmented Generation.
    
    Combines vector similarity search with language model generation
    to provide contextually-aware responses.
    """
    
    def __init__(self):
        """Initialize RAG service with dependencies."""
        self.settings = get_settings()
        self.pinecone_service = get_pinecone_service()
        self.openai_client = AsyncOpenAI(
            api_key=self.settings.openai_api_key
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the RAG service and its dependencies.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize Pinecone index
            success = await self.pinecone_service.initialize_index()
            if not success:
                print("❌ Failed to initialize Pinecone index")
                return False
            
            print("✅ RAG service initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG service: {e}")
            return False
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the knowledge base.
        
        Args:
            documents (List[Dict]): List of documents with 'id', 'text', and optional 'metadata'
            
        Returns:
            bool: True if documents added successfully, False otherwise
        """
        try:
            # Process documents into chunks if they're large
            processed_docs = []
            
            for doc in documents:
                chunks = self._chunk_document(
                    doc['text'], 
                    doc['id'], 
                    doc.get('metadata', {})
                )
                processed_docs.extend(chunks)
            
            # Store chunks in Pinecone
            success = await self.pinecone_service.store_documents(processed_docs)
            
            if success:
                print(f"✅ Added {len(documents)} documents ({len(processed_docs)} chunks)")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False
    
    async def chat_with_context(self, user_message: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate a response using RAG - retrieve relevant context and generate response.
        
        Args:
            user_message (str): User's message/question
            chat_history (List[Dict]): Previous chat messages for context
            
        Returns:
            Dict: Response with generated text, sources, and metadata
        """
        try:
            # Step 1: Retrieve relevant documents
            relevant_docs = await self.pinecone_service.similarity_search(
                query=user_message,
                top_k=self.settings.rag_top_k,
                min_score=self.settings.rag_min_score
            )
            
            # Step 2: Prepare context from retrieved documents
            context = self._prepare_context(relevant_docs)
            
            # Step 3: Prepare messages for OpenAI
            messages = self._prepare_messages(user_message, context, chat_history)
            
            # Step 4: Generate response with OpenAI
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature
            )
            
            # Step 5: Format and return response
            return {
                "response": response.choices[0].message.content,
                "model_used": self.settings.openai_model,
                "sources_used": len(relevant_docs),
                "sources": [
                    {
                        "id": doc["id"],
                        "score": doc["score"],
                        "metadata": doc["metadata"]
                    }
                    for doc in relevant_docs
                ],
                "context_length": len(context)
            }
            
        except Exception as e:
            print(f"❌ RAG chat failed: {e}")
            return {
                "error": f"RAG chat failed: {str(e)}",
                "response": "I apologize, but I'm having trouble accessing my knowledge base right now. Please try again.",
                "model_used": self.settings.openai_model,
                "sources_used": 0,
                "sources": []
            }
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dict: Knowledge base statistics
        """
        try:
            pinecone_stats = await self.pinecone_service.get_index_stats()
            
            return {
                "total_documents": pinecone_stats.get("total_vectors", 0),
                "index_dimension": pinecone_stats.get("dimension", 0),
                "index_fullness": pinecone_stats.get("index_fullness", 0),
                "embedding_model": self.settings.openai_embedding_model,
                "chat_model": self.settings.openai_model,
                "rag_settings": {
                    "top_k": self.settings.rag_top_k,
                    "min_score": self.settings.rag_min_score,
                    "chunk_size": self.settings.chunk_size,
                    "chunk_overlap": self.settings.chunk_overlap
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get knowledge base stats: {e}")
            return {"error": str(e)}
    
    async def clear_knowledge_base(self) -> bool:
        """
        Clear all documents from the knowledge base.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            success = await self.pinecone_service.clear_index()
            if success:
                print("✅ Knowledge base cleared")
            return success
            
        except Exception as e:
            print(f"❌ Failed to clear knowledge base: {e}")
            return False
    
    def _chunk_document(self, text: str, doc_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split document into chunks for better vector search.
        
        Args:
            text (str): Document text
            doc_id (str): Document ID
            metadata (Dict): Document metadata
            
        Returns:
            List[Dict]: List of document chunks
        """
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        # Simple chunking strategy - split by characters with overlap
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary if possible
            if end < len(text) and '.' in chunk_text:
                last_period = chunk_text.rfind('.')
                if last_period > chunk_size * 0.7:  # At least 70% of chunk size
                    end = start + last_period + 1
                    chunk_text = text[start:end]
            
            chunk_id = f"{doc_id}_chunk_{chunk_num}"
            chunks.append({
                "id": chunk_id,
                "text": chunk_text.strip(),
                "metadata": {
                    **metadata,
                    "parent_doc_id": doc_id,
                    "chunk_number": chunk_num,
                    "chunk_start": start,
                    "chunk_end": end
                }
            })
            
            # Move start position with overlap
            start = end - chunk_overlap
            chunk_num += 1
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _prepare_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from retrieved documents.
        
        Args:
            relevant_docs (List[Dict]): Retrieved documents
            
        Returns:
            str: Formatted context string
        """
        if not relevant_docs:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"Context {i} (relevance: {doc['score']:.2f}):\n{doc['text']}")
        
        return "\n\n".join(context_parts)
    
    def _prepare_messages(self, user_message: str, context: str, chat_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """
        Prepare messages array for OpenAI chat completion.
        
        Args:
            user_message (str): Current user message
            context (str): Retrieved context
            chat_history (List[Dict]): Previous chat messages
            
        Returns:
            List[Dict]: Formatted messages for OpenAI
        """
        messages = []
        
        # System message with RAG instructions
        system_prompt = f"""You are a helpful assistant for a software developer's portfolio website. 
You have access to relevant context from the developer's knowledge base.

Use the following context to answer the user's question. If the context doesn't contain 
relevant information, you can still provide a helpful response based on your general knowledge,
but mention that you don't have specific information from the developer's materials.

Context:
{context}

Instructions:
- Provide accurate, helpful responses
- Reference the context when relevant
- Be conversational and engaging
- If asked about the developer's work, projects, or experience, use the provided context
- Keep responses concise but informative"""

        messages.append({"role": "system", "content": system_prompt})
        
        # Add chat history if provided (keep it reasonable)
        if chat_history:
            # Limit history to last 10 messages to avoid token limits
            recent_history = chat_history[-10:]
            for msg in recent_history:
                messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages


# Singleton instance for easy importing
_rag_service = None

def get_rag_service() -> RAGService:
    """
    Get singleton RAGService instance.
    
    Returns:
        RAGService: Singleton service instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service