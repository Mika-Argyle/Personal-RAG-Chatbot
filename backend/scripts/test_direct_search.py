#!/usr/bin/env python3
"""Test direct Pinecone search to bypass our similarity_search method."""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pinecone_service import get_pinecone_service


async def test_direct_search():
    """Test direct Pinecone query."""
    
    pinecone_service = get_pinecone_service()
    await pinecone_service.initialize_index()
    
    # Test query
    query = "What are Mika's technical skills?"
    print(f"🔍 Testing query: {query}")
    
    # Create embedding
    embedding = await pinecone_service.create_embedding(query)
    print(f"✅ Created embedding: {len(embedding)} dimensions")
    
    # Direct Pinecone query
    raw_results = pinecone_service.index.query(
        vector=embedding,
        top_k=10,
        include_metadata=True
    )
    
    print(f"📋 Direct Pinecone results: {len(raw_results.matches)} matches")
    for i, match in enumerate(raw_results.matches, 1):
        print(f"  {i}. ID: {match.id}")
        print(f"     Score: {match.score:.4f}")
        if hasattr(match, 'metadata') and match.metadata:
            text = match.metadata.get('text', 'No text')
            print(f"     Text: {text[:100]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_direct_search())