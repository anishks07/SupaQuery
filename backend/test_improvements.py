#!/usr/bin/env python3
"""
Test script for GraphRAG v2 improvements
Tests the AI Router and enhanced query classification
"""

import asyncio
from app.services.graph_rag_v2 import GraphRAGService

async def test_queries():
    """Test various query types"""
    
    print("=" * 70)
    print("🧪 Testing GraphRAG v2 Improvements")
    print("=" * 70)
    
    # Initialize service
    service = GraphRAGService()
    
    # Test queries
    test_cases = [
        {
            "query": "Hi",
            "expected_strategy": "direct_reply",
            "description": "Greeting (should be instant, no retrieval)"
        },
        {
            "query": "What can you do?",
            "expected_strategy": "direct_reply",
            "description": "Meta question (should be instant)"
        },
        {
            "query": "Who are the key people mentioned?",
            "expected_strategy": "retrieve",
            "expected_type": "entity",
            "description": "Entity query (should list people)"
        },
        {
            "query": "What are the key dates and events?",
            "expected_strategy": "retrieve",
            "expected_type": "date",
            "description": "Date query (should list dates)"
        },
        {
            "query": "Summarize the document",
            "expected_strategy": "retrieve",
            "expected_type": "summary",
            "description": "Summary query"
        },
        {
            "query": "More",
            "expected_strategy": "clarify",
            "description": "Vague query (should ask for clarification)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"Test {i}: {test['description']}")
        print(f"Query: '{test['query']}'")
        print("-" * 70)
        
        try:
            import time
            start_time = time.time()
            
            result = await service.query(test['query'], document_ids=None, top_k=5)
            
            elapsed = time.time() - start_time
            
            # Check strategy
            strategy = result.get('strategy', 'unknown')
            query_type = result.get('query_type', 'N/A')
            answer = result.get('answer', '')
            
            print(f"✓ Strategy: {strategy}")
            print(f"✓ Query Type: {query_type}")
            print(f"✓ Response Time: {elapsed:.2f}s")
            print(f"\nAnswer Preview:")
            print(answer[:300] + "..." if len(answer) > 300 else answer)
            
            # Validation
            if 'expected_strategy' in test:
                if strategy == test['expected_strategy']:
                    print(f"\n✅ PASS: Strategy matches expected ({strategy})")
                else:
                    print(f"\n❌ FAIL: Expected {test['expected_strategy']}, got {strategy}")
            
            if 'expected_type' in test:
                if query_type == test['expected_type']:
                    print(f"✅ PASS: Query type matches expected ({query_type})")
                else:
                    print(f"❌ FAIL: Expected {test['expected_type']}, got {query_type}")
            
            # Performance check
            if strategy == 'direct_reply' and elapsed > 0.5:
                print(f"⚠️  WARNING: Direct reply took {elapsed:.2f}s (should be instant)")
            elif strategy == 'direct_reply' and elapsed < 0.5:
                print(f"⚡ EXCELLENT: Direct reply was instant ({elapsed:.2f}s)")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("🎉 Testing Complete!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_queries())
