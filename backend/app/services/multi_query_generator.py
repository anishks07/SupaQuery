"""
Multi-Query Generator Service
Generates multiple refined queries from a single user query for better retrieval coverage.
This improves recall by capturing different aspects and phrasings of the user's intent.
"""

import os
from typing import List, Dict, Any
import requests


class MultiQueryGenerator:
    """
    Generates multiple variations of a query to improve retrieval.
    Uses LLM to create diverse but related queries.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        print("✅ MultiQueryGenerator initialized")
    
    def generate_queries(self, original_query: str, num_queries: int = 3) -> List[str]:
        """
        Generate multiple query variations from the original query.
        
        Args:
            original_query: The user's original question
            num_queries: Number of alternative queries to generate (default: 3)
            
        Returns:
            List of queries including the original and generated variations
        """
        
        # Start with the original query
        queries = [original_query]
        
        # Generate variations using LLM
        prompt = self._create_multi_query_prompt(original_query, num_queries)
        
        try:
            generated_text = self._call_ollama(prompt, max_tokens=300)
            
            # Parse the generated queries
            variations = self._parse_generated_queries(generated_text)
            
            # Add non-duplicate variations
            for variation in variations:
                if variation and variation not in queries:
                    queries.append(variation)
            
            # Limit to num_queries + 1 (including original)
            queries = queries[:num_queries + 1]
            
            print(f"📝 Generated {len(queries)} query variations:")
            for i, q in enumerate(queries):
                print(f"   {i+1}. {q}")
            
            return queries
            
        except Exception as e:
            print(f"⚠️  Multi-query generation failed: {e}")
            print(f"   Falling back to original query only")
            return [original_query]
    
    def _create_multi_query_prompt(self, query: str, num_queries: int) -> str:
        """Create a prompt for generating query variations"""
        return f"""You are an AI assistant that helps generate alternative phrasings of questions to improve document search.

Given the user's question, generate {num_queries} alternative versions that:
1. Capture the same intent but use different words
2. Break down complex questions into simpler parts
3. Add context that might be implicit in the original
4. Use synonyms and related terms

Original question: "{query}"

Generate {num_queries} alternative questions, one per line. Do not number them or add any other text.

Alternative questions:"""
    
    def _call_ollama(self, prompt: str, max_tokens: int = 300) -> str:
        """Call Ollama API directly"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # Higher temperature for diversity
                        "num_predict": max_tokens,
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama API call failed: {e}")
    
    def _parse_generated_queries(self, generated_text: str) -> List[str]:
        """Parse the LLM output to extract individual queries"""
        lines = generated_text.strip().split('\n')
        queries = []
        
        for line in lines:
            # Remove numbering, bullets, and extra whitespace
            cleaned = line.strip()
            
            # Remove common prefixes
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*', '•']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            
            # Remove quotes if present
            if cleaned.startswith('"') and cleaned.endswith('"'):
                cleaned = cleaned[1:-1]
            if cleaned.startswith("'") and cleaned.endswith("'"):
                cleaned = cleaned[1:-1]
            
            # Only add non-empty queries
            if cleaned and len(cleaned) > 10:  # Minimum length filter
                queries.append(cleaned)
        
        return queries
    
    def generate_with_context(
        self, 
        original_query: str, 
        conversation_history: List[Dict[str, str]] = None,
        num_queries: int = 3
    ) -> List[str]:
        """
        Generate queries with conversation context for better understanding.
        
        Args:
            original_query: Current user question
            conversation_history: Previous messages in the conversation
            num_queries: Number of variations to generate
            
        Returns:
            List of query variations
        """
        
        if not conversation_history:
            return self.generate_queries(original_query, num_queries)
        
        # Build context from recent conversation
        context_lines = []
        for msg in conversation_history[-3:]:  # Last 3 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                context_lines.append(f"{role}: {content}")
        
        context = "\n".join(context_lines)
        
        # Enhanced prompt with context
        prompt = f"""You are an AI assistant that helps generate alternative phrasings of questions to improve document search.

Conversation context:
{context}

Current question: "{original_query}"

Generate {num_queries} alternative versions of the current question that:
1. Consider the conversation context
2. Use different words but capture the same intent
3. Break down complex questions into simpler parts
4. Add implicit context from the conversation

Alternative questions (one per line, no numbering):"""

        try:
            generated_text = self._call_ollama(prompt, max_tokens=300)
            variations = self._parse_generated_queries(generated_text)
            
            queries = [original_query]
            for variation in variations:
                if variation and variation not in queries:
                    queries.append(variation)
            
            return queries[:num_queries + 1]
            
        except Exception as e:
            print(f"⚠️  Context-aware multi-query generation failed: {e}")
            return self.generate_queries(original_query, num_queries)


# Singleton instance
_multi_query_generator = None

def get_multi_query_generator() -> MultiQueryGenerator:
    """Get the singleton MultiQueryGenerator instance"""
    global _multi_query_generator
    if _multi_query_generator is None:
        _multi_query_generator = MultiQueryGenerator()
    return _multi_query_generator
