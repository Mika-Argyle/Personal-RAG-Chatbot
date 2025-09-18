#!/usr/bin/env python3
"""
Knowledge Base Seeding Script

This script seeds the RAG knowledge base with sample portfolio documents.
Run this once to populate the vector database for testing and demonstration.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_knowledge_base.py
"""

import asyncio
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import get_rag_service


async def seed_knowledge_base():
    """Seed the knowledge base with sample portfolio documents."""
    
    rag_service = get_rag_service()
    
    # Initialize the RAG service
    print("🚀 Initializing RAG service...")
    success = await rag_service.initialize()
    if not success:
        print("❌ Failed to initialize RAG service")
        return False
    
    # Sample portfolio documents
    sample_documents = [
        {
            "id": "bio",
            "text": """Mika Argyle is a Machine Learning Engineer with expertise in AI systems, vector databases, and full-stack development. 
            She has experience building RAG (Retrieval-Augmented Generation) systems using OpenAI and Pinecone, developing FastAPI applications, 
            and implementing comprehensive testing infrastructures. Her technical skills include Python, TypeScript, React, and modern AI/ML technologies. 
            She follows professional development practices including test-driven development, proper version control, and production-ready code standards.""",
            "metadata": {"type": "bio", "category": "about"}
        },
        {
            "id": "skills",
            "text": """Technical Skills: Python, FastAPI, OpenAI API, Pinecone Vector Database, RAG Systems, Machine Learning, 
            Async Programming, Pytest Testing, Docker, Git, TypeScript, React, REST APIs, Database Design, 
            Cloud Services (AWS), Vector Embeddings, Natural Language Processing, Full-Stack Development, 
            Test-Driven Development, Agile Methodologies, System Architecture.""",
            "metadata": {"type": "skills", "category": "technical"}
        },
        {
            "id": "rag_project",
            "text": """Personal RAG Chatbot Project: Built a production-ready Retrieval-Augmented Generation chatbot using FastAPI, 
            OpenAI GPT-4, and Pinecone vector database. Features include intelligent document chunking, similarity search 
            with configurable thresholds, async operations, comprehensive error handling, and extensive test coverage. 
            The system uses OpenAI embeddings for vector storage and implements professional software engineering practices 
            including singleton patterns, dependency injection, and mock-based testing.""",
            "metadata": {"type": "project", "category": "portfolio", "tech_stack": "Python,FastAPI,OpenAI,Pinecone"}
        },
        {
            "id": "testing_expertise",
            "text": """Testing and Quality Assurance: Experienced in implementing comprehensive testing infrastructures using pytest 
            and pytest-asyncio. Skilled in mock-based testing for external API integrations, async testing patterns, 
            and achieving high test coverage. Implements professional testing practices including unit tests, integration tests, 
            edge case coverage, and proper test organization with fixtures and parameterization.""",
            "metadata": {"type": "expertise", "category": "testing"}
        },
        {
            "id": "ai_ml_experience",
            "text": """AI/ML Engineering Experience: Hands-on experience with OpenAI APIs including GPT-4 and embedding models, 
            vector database operations, similarity search algorithms, and RAG system architecture. Understands 
            embedding spaces, cosine similarity, prompt engineering, and context management for large language models. 
            Experience with document processing, text chunking strategies, and optimizing retrieval systems for accuracy.""",
            "metadata": {"type": "experience", "category": "ai_ml"}
        }
    ]
    
    # Add documents to knowledge base
    print(f"📚 Adding {len(sample_documents)} documents to knowledge base...")
    success = await rag_service.add_documents(sample_documents)
    
    if success:
        print("✅ Successfully seeded knowledge base!")
        
        # Get stats to confirm
        stats = await rag_service.get_knowledge_base_stats()
        print(f"📊 Knowledge base now contains {stats.get('total_documents', 0)} document chunks")
        print(f"🎯 Index fullness: {stats.get('index_fullness', 0):.2%}")
        
        return True
    else:
        print("❌ Failed to seed knowledge base")
        return False


async def test_rag_chat():
    """Test the RAG chat functionality with a sample query."""
    rag_service = get_rag_service()
    
    print("\n🧪 Testing RAG chat functionality...")
    
    test_queries = [
        "What are Mika's technical skills?",
        "Tell me about the RAG project",
        "What testing experience does Mika have?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        response = await rag_service.chat_with_context(query)
        
        print(f"🤖 Response: {response['response'][:200]}...")
        print(f"📖 Sources used: {response['sources_used']}")
        
        if response['sources']:
            print("📋 Source documents:")
            for source in response['sources']:
                print(f"  - {source['id']} (score: {source['score']:.2f})")


if __name__ == "__main__":
    print("🌱 Personal RAG Chatbot - Knowledge Base Seeding")
    print("=" * 50)
    
    try:
        # Seed the knowledge base
        success = asyncio.run(seed_knowledge_base())
        
        if success:
            # Test RAG functionality
            asyncio.run(test_rag_chat())
            print("\n🎉 Knowledge base seeding and testing completed successfully!")
        else:
            print("\n❌ Knowledge base seeding failed")
            
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")