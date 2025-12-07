import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import re

load_dotenv()

class RAGEvaluator:
    """
    Enhanced RAG evaluator with:
    - Structured JSON output for reliable parsing
    - More detailed evaluation criteria
    - Transparent reasoning
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.0  # Zero temperature for consistent evaluation
        )
    
    def _safe_parse_json(self, text: str) -> Dict:
        """Safely extract and parse JSON from LLM response"""
        try:
            # Try direct parsing first
            return json.loads(text)
        except:
            # Look for JSON in markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Look for JSON without code blocks
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            # Return default structure if parsing fails
            return {"score": 0.0, "verdict": "ERROR", "reasoning": "Failed to parse evaluation"}
    
    def evaluate_context_relevance(self, query: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Evaluates if retrieved contexts are relevant to the query using structured output
        """
        contexts_text = "\n\n".join([f"Context {i+1}:\n{ctx[:500]}..." for i, ctx in enumerate(contexts)])
        
        prompt = f"""Evaluate how relevant each retrieved context is to the user's query. 

QUERY: {query}

CONTEXTS:
{contexts_text}

For each context, rate its relevance on a scale of 0.0 to 1.0 where:
- 0.0-0.3: Completely irrelevant
- 0.4-0.6: Somewhat relevant but missing key information
- 0.7-0.8: Relevant with some useful information
- 0.9-1.0: Highly relevant and directly answers the query

Respond ONLY with a JSON object in this exact format:
{{
  "individual_scores": [0.9, 0.7, 0.5, 0.3, 0.2],
  "average_score": 0.52,
  "reasoning": "Context 1 and 2 directly address the budget question with specific numbers. Context 3 mentions budget but lacks details. Contexts 4 and 5 discuss unrelated project timeline information.",
  "verdict": "PASS or FAIL (PASS if average >= 0.7)"
}}"""
        
        response = self.llm.invoke(prompt)
        result = self._safe_parse_json(response.content)
        
        # Ensure all fields exist
        score = result.get("average_score", 0.0)
        return {
            "metric": "context_relevance",
            "score": score,
            "individual_scores": result.get("individual_scores", []),
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "verdict": "PASS" if score >= 0.7 else "FAIL",
            "threshold": 0.7
        }
    
    def evaluate_faithfulness(self, answer: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Evaluates if the answer is grounded in the contexts (checks for hallucinations)
        """
        contexts_text = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
        
        prompt = f"""Evaluate if the answer is faithful to the provided contexts. Check each claim in the answer against the contexts.

CONTEXTS:
{contexts_text}

ANSWER: {answer}

Analyze each statement in the answer:
- Is it directly supported by the contexts?
- Is it a reasonable inference from the contexts?
- Is it added information not in contexts (hallucination)?

Respond ONLY with a JSON object:
{{
  "score": 0.85,
  "supported_claims": ["Budget is $500K (from Context 1)", "Timeline is 6 months (from Context 2)"],
  "unsupported_claims": ["The project includes 10 team members (NOT mentioned in contexts)"],
  "reasoning": "Most claims are well-supported, but team size claim appears to be hallucinated",
  "verdict": "FAITHFUL or UNFAITHFUL (FAITHFUL if score >= 0.8)"
}}"""
        
        response = self.llm.invoke(prompt)
        result = self._safe_parse_json(response.content)
        
        score = result.get("score", 0.0)
        return {
            "metric": "faithfulness",
            "score": score,
            "supported_claims": result.get("supported_claims", []),
            "unsupported_claims": result.get("unsupported_claims", []),
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "verdict": "FAITHFUL" if score >= 0.8 else "UNFAITHFUL",
            "threshold": 0.8
        }
    
    def evaluate_answer_relevance(self, query: str, answer: str) -> Dict[str, Any]:
        """
        Evaluates if the answer actually addresses the user's question
        """
        prompt = f"""Evaluate if the answer is relevant to and addresses the user's query.

QUERY: {query}

ANSWER: {answer}

Consider:
- Does the answer directly address what was asked?
- Is the answer complete or does it miss important aspects of the question?
- Does it contain unnecessary information not related to the query?

Respond ONLY with a JSON object:
{{
  "score": 0.9,
  "addresses_query": true,
  "missing_aspects": ["Doesn't mention the deadline which was part of the question"],
  "irrelevant_content": ["Discusses team structure which wasn't asked about"],
  "reasoning": "Answer provides the requested budget information clearly but adds unnecessary team details",
  "verdict": "RELEVANT or IRRELEVANT (RELEVANT if score >= 0.7)"
}}"""
        
        response = self.llm.invoke(prompt)
        result = self._safe_parse_json(response.content)
        
        score = result.get("score", 0.0)
        return {
            "metric": "answer_relevance",
            "score": score,
            "addresses_query": result.get("addresses_query", False),
            "missing_aspects": result.get("missing_aspects", []),
            "irrelevant_content": result.get("irrelevant_content", []),
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "verdict": "RELEVANT" if score >= 0.7 else "IRRELEVANT",
            "threshold": 0.7
        }
    
    def evaluate_citation_quality(self, answer: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        NEW: Evaluates if the answer properly cites its sources
        """
        sources_text = "\n".join([f"- {s['file']}, Page {s['page']}" for s in sources])
        
        prompt = f"""Evaluate how well the answer cites its sources.

AVAILABLE SOURCES:
{sources_text}

ANSWER: {answer}

Check:
- Does the answer reference specific sources when making claims?
- Are the citations appropriate and helpful?
- Can we trace claims back to sources?

Respond ONLY with a JSON object:
{{
  "score": 0.75,
  "has_citations": true,
  "citation_examples": ["According to Source 1..."],
  "uncited_claims": ["The deadline claim lacks a source reference"],
  "reasoning": "Answer cites sources for budget info but not for deadline",
  "verdict": "GOOD or POOR (GOOD if score >= 0.6)"
}}"""
        
        response = self.llm.invoke(prompt)
        result = self._safe_parse_json(response.content)
        
        score = result.get("score", 0.0)
        return {
            "metric": "citation_quality",
            "score": score,
            "has_citations": result.get("has_citations", False),
            "citation_examples": result.get("citation_examples", []),
            "uncited_claims": result.get("uncited_claims", []),
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "verdict": "GOOD" if score >= 0.6 else "POOR",
            "threshold": 0.6
        }
    
    def comprehensive_evaluation(self, query: str, answer: str, 
                                 contexts: List[str], 
                                 sources: List[Dict]) -> Dict[str, Any]:
        """
        Runs all evaluation metrics with transparent reasoning
        """
        print("\n🔍 Running RAG Evaluation...")
        
        # Run all metrics
        context_rel = self.evaluate_context_relevance(query, contexts)
        print(f"  ✓ Context Relevance: {context_rel['score']:.2f}")
        
        faithfulness = self.evaluate_faithfulness(answer, contexts)
        print(f"  ✓ Faithfulness: {faithfulness['score']:.2f}")
        
        answer_rel = self.evaluate_answer_relevance(query, answer)
        print(f"  ✓ Answer Relevance: {answer_rel['score']:.2f}")
        
        citation_qual = self.evaluate_citation_quality(answer, sources)
        print(f"  ✓ Citation Quality: {citation_qual['score']:.2f}")
        
        # Calculate weighted overall score
        overall_score = (
            context_rel["score"] * 0.25 +      # 25% - Are we retrieving the right info?
            faithfulness["score"] * 0.35 +      # 35% - Is the answer grounded? (most critical)
            answer_rel["score"] * 0.25 +        # 25% - Does it answer the question?
            citation_qual["score"] * 0.15       # 15% - Are sources properly cited?
        )
        
        # Generate detailed recommendations
        recommendations = self._generate_detailed_recommendations(
            context_rel, faithfulness, answer_rel, citation_qual
        )
        
        return {
            "query": query,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "sources": sources,
            "metrics": {
                "context_relevance": context_rel,
                "faithfulness": faithfulness,
                "answer_relevance": answer_rel,
                "citation_quality": citation_qual
            },
            "overall_score": round(overall_score, 3),
            "overall_verdict": "PASS" if overall_score >= 0.7 else "FAIL",
            "recommendations": recommendations
        }
    
    def _generate_detailed_recommendations(self, context_rel: Dict, 
                                          faithfulness: Dict, 
                                          answer_rel: Dict,
                                          citation_qual: Dict) -> List[str]:
        """Generate specific, actionable recommendations"""
        recommendations = []
        
        # Context relevance issues
        if context_rel["score"] < 0.7:
            recommendations.append(
                f"⚠️ LOW CONTEXT RELEVANCE ({context_rel['score']:.2f}): "
                f"{context_rel['reasoning']}. "
                "Try: Increase Top K to 8-10, reduce chunk size to 600-800, or use better embeddings model."
            )
        
        # Faithfulness issues (most critical)
        if faithfulness["score"] < 0.8:
            unsupported = faithfulness.get("unsupported_claims", [])
            recommendations.append(
                f"🚨 LOW FAITHFULNESS ({faithfulness['score']:.2f}): "
                f"{faithfulness['reasoning']}. "
                f"Unsupported claims: {', '.join(unsupported) if unsupported else 'See details'}. "
                "Try: Lower temperature to 0.3-0.5, improve prompt instructions, or check if documents contain the required info."
            )
        
        # Answer relevance issues
        if answer_rel["score"] < 0.7:
            missing = answer_rel.get("missing_aspects", [])
            recommendations.append(
                f"⚠️ LOW ANSWER RELEVANCE ({answer_rel['score']:.2f}): "
                f"{answer_rel['reasoning']}. "
                f"Missing: {', '.join(missing) if missing else 'See details'}. "
                "Try: Rephrase query to be more specific, or check if documents actually contain the answer."
            )
        
        # Citation quality issues
        if citation_qual["score"] < 0.6:
            recommendations.append(
                f"📄 POOR CITATION QUALITY ({citation_qual['score']:.2f}): "
                f"{citation_qual['reasoning']}. "
                "Try: Enhance prompt to explicitly require source citations for each claim."
            )
        
        # If everything is good
        if not recommendations:
            recommendations.append(
                f"✅ EXCELLENT RESPONSE! All metrics above threshold. "
                f"Overall score: {context_rel['score'] * 0.25 + faithfulness['score'] * 0.35 + answer_rel['score'] * 0.25 + citation_qual['score'] * 0.15:.2f}"
            )
        
        return recommendations