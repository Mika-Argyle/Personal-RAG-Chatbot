#!/usr/bin/env python3
"""
Knowledge Base Seeding Script
Seeds the Pinecone vector database with portfolio content for RAG chatbot.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService
from app.services.pinecone_service import PineconeService
from app.config import get_settings

# Portfolio content to seed the knowledge base
PORTFOLIO_CONTENT = [
    {
        "title": "Professional Summary",
        "content": """
        Experienced Machine Learning Engineer and AI Developer with expertise in:
        - RAG (Retrieval-Augmented Generation) systems with vector databases
        - Python backend development with FastAPI and async programming
        - Modern frontend development with React and TypeScript
        - Vector databases (Pinecone) and embedding models (OpenAI)
        - Full-stack AI application development and deployment
        - Professional testing with pytest and comprehensive coverage
        - Modern development practices including Git, Docker, and CI/CD
        """
    },
    {
        "title": "Technical Skills",
        "content": """
        Programming Languages:
        - Python (Advanced): FastAPI, async/await, Pydantic, pytest
        - TypeScript/JavaScript: React, Node.js, modern ES6+ features
        - SQL: PostgreSQL, database design and optimization
        
        Machine Learning & AI:
        - OpenAI GPT models and embedding APIs
        - Vector databases and similarity search (Pinecone)
        - RAG system architecture and implementation
        - Natural language processing and text chunking
        - Prompt engineering and context optimization
        
        Backend Technologies:
        - FastAPI with async programming patterns
        - RESTful API design and implementation
        - Database integration (PostgreSQL, Redis)
        - Authentication and security best practices
        - Comprehensive testing with mocking and fixtures
        
        Frontend Technologies:
        - React with hooks and functional components
        - TypeScript for type-safe development
        - Modern CSS with glassmorphism and responsive design
        - State management and API integration
        
        Development Tools:
        - Git version control with professional workflows
        - Docker containerization and deployment
        - pytest for comprehensive test coverage
        - Professional documentation and code quality
        """
    },
    {
        "title": "RAG Chatbot Project",
        "content": """
        Built a sophisticated Personal RAG Chatbot demonstrating full-stack AI development:
        
        Backend Architecture:
        - FastAPI backend with async Python programming
        - Pinecone vector database integration for semantic search
        - OpenAI GPT-4 and embedding model integration
        - Professional RAG pipeline with document chunking and retrieval
        - Comprehensive testing suite with 70+ tests and 91% pass rate
        - Singleton pattern services and proper error handling
        
        Frontend Implementation:
        - Modern React TypeScript application with 600+ lines of code
        - Professional glassmorphism UI design with gradient backgrounds
        - Real-time chat interface with auto-scroll and animations
        - Backend integration with connection status monitoring
        - Responsive design supporting mobile and desktop
        
        Technical Achievements:
        - Type-safe communication between frontend and backend
        - Context-aware RAG responses with similarity threshold filtering
        - Professional development workflow with hot reload and testing
        - Production-ready architecture with security-first design
        - Complete documentation and progress tracking
        
        This project demonstrates senior-level engineering skills including:
        - System architecture and design patterns
        - Modern Python and TypeScript development
        - AI/ML integration with production considerations
        - Professional testing and quality assurance
        - User experience design and responsive interfaces
        """
    },
    {
        "title": "Development Philosophy",
        "content": """
        Professional Development Approach:
        - Test-driven development with comprehensive coverage
        - Type-safe programming with TypeScript and Pydantic
        - Security-first design with proper authentication
        - Performance optimization and scalable architecture
        - Clean code principles and maintainable structure
        - Professional documentation and progress tracking
        
        AI/ML Best Practices:
        - Responsible AI development with fallback mechanisms
        - Context-aware systems with proper similarity thresholds
        - Efficient vector storage and retrieval operations
        - Token optimization and cost management
        - Professional prompt engineering techniques
        
        Team Collaboration:
        - Clear git workflows with professional commit messages
        - Comprehensive documentation for knowledge sharing
        - Code review practices and quality standards
        - Agile development with iterative improvements
        - Professional communication and progress reporting
        """
    },
    {
        "title": "Project Portfolio",
        "content": """
        Recent Projects:
        
        1. Personal RAG Chatbot (Current)
           - Full-stack AI application with React + FastAPI
           - Pinecone vector database integration
           - OpenAI GPT-4 and embedding models
           - Professional UI/UX with glassmorphism design
           - Comprehensive testing and documentation
        
        Technical Highlights:
        - 2000+ lines of production code across backend and frontend
        - Type-safe TypeScript and Python implementation
        - Modern async programming patterns
        - Professional testing with mocking and fixtures
        - Security-conscious API design
        - Responsive and accessible user interface
        
        This portfolio demonstrates:
        - Full-stack development capabilities
        - AI/ML system integration expertise
        - Modern development practices and tooling
        - Professional code quality and documentation
        - User experience and interface design skills
        """
    }
]

async def seed_knowledge_base():
    """Seed the knowledge base with portfolio content."""
    print("🌱 Starting knowledge base seeding...")
    
    try:
        # Initialize services
        settings = get_settings()
        pinecone_service = PineconeService()
        rag_service = RAGService()
        
        print("✅ Services initialized")
        
        # Clear existing content (optional)
        # await pinecone_service.delete_all_vectors()
        # print("🗑️  Cleared existing vectors")
        
        # Process and upload documents
        print(f"\n📄 Processing {len(PORTFOLIO_CONTENT)} documents...")
        
        # Prepare documents in the expected format
        documents = []
        for i, doc in enumerate(PORTFOLIO_CONTENT, 1):
            full_text = f"Title: {doc['title']}\n\n{doc['content']}"
            documents.append({
                "id": f"portfolio_{i}",
                "text": full_text,
                "metadata": {
                    "title": doc["title"],
                    "section": f"portfolio_{i}",
                    "document_type": "portfolio"
                }
            })
        
        # Upload all documents at once
        success = await rag_service.add_documents(documents)
        
        if success:
            print(f"✅ Successfully added {len(documents)} documents to knowledge base!")
        else:
            print("❌ Failed to add documents to knowledge base")
            return
        
        # Get statistics
        stats = await rag_service.get_knowledge_base_stats()
        print(f"📈 Knowledge base stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise

async def test_search(query: str = "What are your technical skills?"):
    """Test search functionality with a sample query."""
    print(f"\n🔍 Testing search with query: '{query}'")
    
    try:
        rag_service = RAGService()
        
        # Test full RAG response using the main chat method
        response = await rag_service.chat_with_context(query, [])
        print(f"\n🤖 RAG Response:")
        print(f"   Context used: {response.get('context_used', False)}")
        print(f"   Response: {response['response']}")
        
        # Show sources if available
        if response.get('sources'):
            print(f"   Sources: {len(response['sources'])} documents used")
            for i, source in enumerate(response['sources'][:3], 1):  # Show first 3
                print(f"     {i}. {source[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during search test: {e}")
        raise

async def main():
    """Main function to run seeding and testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Management")
    parser.add_argument("--seed", action="store_true", help="Seed the knowledge base")
    parser.add_argument("--test", action="store_true", help="Test search functionality")
    parser.add_argument("--query", type=str, default="What are your technical skills?", 
                       help="Test query for search")
    
    args = parser.parse_args()
    
    if args.seed:
        await seed_knowledge_base()
    
    if args.test:
        await test_search(args.query)
    
    if not args.seed and not args.test:
        print("Please specify --seed or --test (or both)")
        print("Examples:")
        print("  python seed_knowledge_base.py --seed")
        print("  python seed_knowledge_base.py --test")
        print("  python seed_knowledge_base.py --seed --test")
        print('  python seed_knowledge_base.py --test --query "Tell me about your projects"')

if __name__ == "__main__":
    asyncio.run(main())