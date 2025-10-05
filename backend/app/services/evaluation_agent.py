"""
Evaluation Agent Service
Evaluates the quality and completeness of retrieved answers.
Provides feedback to the routing agent if answers are insufficient.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import requests


class EvaluationAgent:
    """
    Evaluates whether retrieved information adequately answers the user's query.
    Provides feedback for re-routing if needed.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.quality_threshold = 0.7  # Minimum quality score to accept answer
        print("✅ EvaluationAgent initialized")
    
    def evaluate_answer(
        self,
        query: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate the quality and completeness of an answer.
        
        Args:
            query: Original user query
            answer: Generated answer
            retrieved_chunks: Chunks used to generate answer
            sources: Source documents referenced
            
        Returns:
            Dictionary with evaluation results:
            {
                "is_sufficient": bool,
                "quality_score": float (0-1),
                "completeness_score": float (0-1),
                "relevance_score": float (0-1),
                "feedback": str,
                "suggested_improvements": List[str]
            }
        """
        
        print(f"🔍 Evaluating answer quality...")
        
        # Perform multiple evaluation checks
        quality_score = self._evaluate_quality(query, answer)
        completeness_score = self._evaluate_completeness(query, answer)
        relevance_score = self._evaluate_relevance(query, answer, retrieved_chunks)
        
        # Calculate overall score
        overall_score = (quality_score + completeness_score + relevance_score) / 3
        
        # Determine if answer is sufficient
        is_sufficient = overall_score >= self.quality_threshold
        
        # Generate feedback
        feedback, suggestions = self._generate_feedback(
            query, answer, quality_score, completeness_score, relevance_score
        )
        
        result = {
            "is_sufficient": is_sufficient,
            "overall_score": overall_score,
            "quality_score": quality_score,
            "completeness_score": completeness_score,
            "relevance_score": relevance_score,
            "feedback": feedback,
            "suggested_improvements": suggestions,
            "sources_count": len(sources),
            "chunks_count": len(retrieved_chunks)
        }
        
        print(f"   Overall Score: {overall_score:.2f}")
        print(f"   Quality: {quality_score:.2f} | Completeness: {completeness_score:.2f} | Relevance: {relevance_score:.2f}")
        print(f"   Sufficient: {'✅ YES' if is_sufficient else '❌ NO'}")
        
        return result
    
    def _evaluate_quality(self, query: str, answer: str) -> float:
        """
        Evaluate answer quality (coherence, clarity, factuality).
        Uses LLM-based evaluation.
        """
        
        # Quick heuristic checks
        if not answer or len(answer.strip()) < 10:
            return 0.0
        
        if "I don't know" in answer or "cannot answer" in answer.lower():
            return 0.3
        
        if "don't have enough information" in answer.lower():
            return 0.4
        
        # Use LLM for deeper evaluation
        prompt = f"""Evaluate the quality of this answer on a scale of 0 to 10.

Question: {query}

Answer: {answer}

Consider:
- Is the answer coherent and well-structured?
- Is the language clear and professional?
- Does it seem factually sound?
- Is it appropriately detailed?

Respond with ONLY a number between 0 and 10."""

        try:
            score_text = self._call_ollama(prompt, max_tokens=10)
            # Extract number from response
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', score_text)
            if match:
                score = float(match.group(1))
                return min(score / 10.0, 1.0)  # Normalize to 0-1
        except:
            pass
        
        # Fallback: basic heuristic
        if len(answer) > 100:
            return 0.7
        elif len(answer) > 50:
            return 0.5
        else:
            return 0.3
    
    def _evaluate_completeness(self, query: str, answer: str) -> float:
        """
        Evaluate if the answer fully addresses the question.
        """
        
        prompt = f"""Does this answer fully address the question?

Question: {query}

Answer: {answer}

Rate completeness on a scale of 0 to 10:
- 0: Doesn't address the question at all
- 5: Partially answers but missing key information
- 10: Completely answers all aspects of the question

Respond with ONLY a number between 0 and 10."""

        try:
            score_text = self._call_ollama(prompt, max_tokens=10)
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', score_text)
            if match:
                score = float(match.group(1))
                return min(score / 10.0, 1.0)
        except:
            pass
        
        # Fallback: check if answer contains question keywords
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words & answer_words)
        return min(overlap / len(query_words), 1.0) if query_words else 0.5
    
    def _evaluate_relevance(
        self, 
        query: str, 
        answer: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluate if the answer is relevant to the query and based on retrieved content.
        """
        
        if not retrieved_chunks:
            return 0.2  # Low relevance if no chunks retrieved
        
        # Check if answer uses information from chunks
        chunk_texts = [chunk.get('text', '') for chunk in retrieved_chunks]
        all_chunk_text = ' '.join(chunk_texts).lower()
        answer_words = set(answer.lower().split())
        
        # Count how many answer words appear in chunks
        words_from_chunks = sum(1 for word in answer_words if word in all_chunk_text)
        
        if len(answer_words) > 0:
            grounding_score = words_from_chunks / len(answer_words)
        else:
            grounding_score = 0.0
        
        return min(grounding_score * 1.5, 1.0)  # Boost and cap at 1.0
    
    def _generate_feedback(
        self,
        query: str,
        answer: str,
        quality_score: float,
        completeness_score: float,
        relevance_score: float
    ) -> Tuple[str, List[str]]:
        """
        Generate human-readable feedback and suggestions for improvement.
        """
        
        feedback_parts = []
        suggestions = []
        
        if quality_score < 0.6:
            feedback_parts.append("Answer quality is low.")
            suggestions.append("Improve answer coherence and clarity")
        
        if completeness_score < 0.6:
            feedback_parts.append("Answer is incomplete.")
            suggestions.append("Retrieve more relevant information")
            suggestions.append("Try different search queries")
        
        if relevance_score < 0.6:
            feedback_parts.append("Answer not well-grounded in sources.")
            suggestions.append("Ensure answer uses retrieved content")
            suggestions.append("Expand search to more documents")
        
        if not feedback_parts:
            feedback = "Answer meets quality standards."
        else:
            feedback = " ".join(feedback_parts)
        
        if not suggestions:
            suggestions = ["Answer is satisfactory"]
        
        return feedback, suggestions
    
    def _call_ollama(self, prompt: str, max_tokens: int = 100) -> str:
        """Call Ollama API directly"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent evaluation
                        "num_predict": max_tokens,
                    }
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama API call failed: {e}")
    
    def should_retry(self, evaluation: Dict[str, Any]) -> bool:
        """
        Determine if we should retry with different retrieval strategy.
        """
        return not evaluation["is_sufficient"]
    
    def get_retry_strategy(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest a retry strategy based on evaluation feedback.
        
        Returns:
            Dictionary with retry parameters:
            {
                "expand_search": bool,
                "use_entities": bool,
                "increase_top_k": int,
                "refine_query": bool
            }
        """
        
        strategy = {
            "expand_search": False,
            "use_entities": False,
            "increase_top_k": 5,
            "refine_query": False
        }
        
        # If completeness is low, expand search
        if evaluation["completeness_score"] < 0.6:
            strategy["expand_search"] = True
            strategy["increase_top_k"] = 10
        
        # If relevance is low, try entity-based search
        if evaluation["relevance_score"] < 0.6:
            strategy["use_entities"] = True
        
        # If quality is low, refine the query
        if evaluation["quality_score"] < 0.6:
            strategy["refine_query"] = True
        
        return strategy


# Singleton instance
_evaluation_agent = None

def get_evaluation_agent() -> EvaluationAgent:
    """Get the singleton EvaluationAgent instance"""
    global _evaluation_agent
    if _evaluation_agent is None:
        _evaluation_agent = EvaluationAgent()
    return _evaluation_agent
