#!/usr/bin/env python3
"""
Direct Search Script
Quick testing of Pinecone vector database search functionality.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pinecone_service import PineconeService
from app.services.rag_service import RAGService

async def direct_search(query: str, top_k: int = 5, min_score: float = 0.0):
    """Perform direct vector search in Pinecone."""
    print(f"🔍 Direct search query: '{query}'")
    print(f"📊 Parameters: top_k={top_k}, min_score={min_score}")
    
    try:
        # Initialize services
        pinecone_service = PineconeService()
        
        # Perform search using the query string directly
        results = await pinecone_service.similarity_search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )
        
        print(f"\n📋 Search Results ({len(results)} matches):")
        if not results:
            print("   No results found. Try lowering min_score or check if knowledge base is seeded.")
            return
        
        for i, result in enumerate(results, 1):
            score = result.get('score', 0)
            content = result.get('metadata', {}).get('content', 'No content')
            title = result.get('metadata', {}).get('title', 'No title')
            
            print(f"\n   {i}. Score: {score:.4f}")
            print(f"      Title: {title}")
            print(f"      Content: {content[:150]}...")
            if len(content) > 150:
                print("                ...")
    
    except Exception as e:
        print(f"❌ Error during search: {e}")
        raise

async def rag_search(query: str):
    """Test the full RAG pipeline."""
    print(f"\n🤖 RAG Pipeline Test: '{query}'")
    
    try:
        rag_service = RAGService()
        
        # Get context
        context = await rag_service.get_relevant_context(query)
        print(f"📋 Retrieved {len(context)} context chunks")
        
        # Generate response
        response = await rag_service.generate_response(query, [])
        
        print(f"\n💬 Response:")
        print(f"   Context used: {response.get('context_used', False)}")
        print(f"   Response: {response['response']}")
        
    except Exception as e:
        print(f"❌ Error during RAG search: {e}")
        raise

async def knowledge_base_stats():
    """Get knowledge base statistics."""
    print("📊 Knowledge Base Statistics")
    
    try:
        pinecone_service = PineconeService()
        rag_service = RAGService()
        
        # Get index stats
        index_stats = await pinecone_service.get_index_stats()
        print(f"   Index stats: {index_stats}")
        
        # Get RAG service stats
        rag_stats = await rag_service.get_knowledge_base_stats()
        print(f"   RAG stats: {rag_stats}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        raise

# Common test queries
TEST_QUERIES = [
    "What are your technical skills?",
    "Tell me about your Python experience",
    "What AI and machine learning projects have you worked on?",
    "Describe your frontend development skills",
    "What is your experience with React and TypeScript?",
    "Tell me about your RAG chatbot project",
    "What testing frameworks do you use?",
    "Describe your development philosophy"
]

async def main():
    """Main function for direct search testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Direct Search Testing")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum similarity score")
    parser.add_argument("--rag", action="store_true", help="Test full RAG pipeline")
    parser.add_argument("--stats", action="store_true", help="Show knowledge base statistics")
    parser.add_argument("--test-all", action="store_true", help="Test with common queries")
    
    args = parser.parse_args()
    
    # Show stats first if requested
    if args.stats:
        await knowledge_base_stats()
        print()
    
    # Test with all common queries
    if args.test_all:
        print("🧪 Testing with common queries...")
        for query in TEST_QUERIES:
            print(f"\n{'='*60}")
            await direct_search(query, top_k=3, min_score=0.7)
            await asyncio.sleep(0.5)  # Brief pause between requests
        return
    
    # Single query test
    if args.query:
        await direct_search(args.query, args.top_k, args.min_score)
        
        if args.rag:
            await rag_search(args.query)
    else:
        # Interactive mode
        print("🔍 Direct Search Interactive Mode")
        print("Available commands:")
        print("  search <query> - Search for query")
        print("  rag <query>    - Test RAG pipeline")
        print("  stats          - Show statistics")
        print("  test           - Run common test queries")
        print("  quit           - Exit")
        
        while True:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() == 'stats':
                    await knowledge_base_stats()
                elif command.lower() == 'test':
                    for query in TEST_QUERIES[:3]:  # Test first 3
                        print(f"\n{'='*40}")
                        await direct_search(query, top_k=3, min_score=0.7)
                elif command.startswith('search '):
                    query = command[7:]
                    await direct_search(query, top_k=5, min_score=0.0)
                elif command.startswith('rag '):
                    query = command[4:]
                    await rag_search(query)
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())