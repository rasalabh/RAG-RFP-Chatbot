import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class RAGEvaluator:
    """
    Evaluates RAG system performance across multiple dimensions:
    - Context Relevance: Are retrieved chunks relevant to the query?
    - Faithfulness: Is the answer grounded in the retrieved context?
    - Answer Relevance: Does the answer address the query?
    - Noise Robustness: Can the system handle irrelevant chunks?
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1  # Low temperature for consistent evaluation
        )
    
    def evaluate_context_relevance(self, query: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Evaluates if retrieved contexts are relevant to the query.
        Returns a score from 0-1 and reasons.
        """
        contexts_text = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])
        
        prompt = f"""Evaluate the relevance of the following contexts to the query.
Rate each context on a scale of 0-1 (0=completely irrelevant, 1=highly relevant).

Query: {query}

{contexts_text}

Provide your evaluation in this format:
Context 1: [score] - [brief reason]
Context 2: [score] - [brief reason]
...
Overall Score: [average score]
"""
        
        response = self.llm.invoke(prompt)
        
        # Parse the response
        lines = response.content.strip().split('\n')
        scores = []
        reasons = []
        
        for line in lines:
            if 'Context' in line and ':' in line:
                try:
                    score_part = line.split(':')[1].split('-')[0].strip()
                    score = float(score_part)
                    reason = line.split('-', 1)[1].strip() if '-' in line else ""
                    scores.append(score)
                    reasons.append(reason)
                except:
                    continue
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "metric": "context_relevance",
            "score": overall_score,
            "individual_scores": scores,
            "reasons": reasons,
            "verdict": "PASS" if overall_score >= 0.7 else "FAIL"
        }
    
    def evaluate_faithfulness(self, answer: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Evaluates if the answer is faithful to the retrieved contexts.
        Checks for hallucinations and unsupported claims.
        """
        contexts_text = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])
        
        prompt = f"""Evaluate if the answer is faithful to the provided contexts.
Check if all claims in the answer are supported by the contexts.
Identify any hallucinations or unsupported statements.

Contexts:
{contexts_text}

Answer: {answer}

Provide evaluation:
1. Faithfulness Score (0-1): [score]
2. Supported Claims: [list]
3. Unsupported Claims (if any): [list]
4. Verdict: FAITHFUL or UNFAITHFUL
"""
        
        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        # Extract score
        score = 0.0
        if "Faithfulness Score" in content:
            try:
                score_line = [l for l in content.split('\n') if 'Faithfulness Score' in l][0]
                score = float(score_line.split(':')[1].strip().split()[0])
            except:
                score = 0.5
        
        verdict = "FAITHFUL" if score >= 0.8 else "UNFAITHFUL"
        
        return {
            "metric": "faithfulness",
            "score": score,
            "evaluation": content,
            "verdict": verdict
        }
    
    def evaluate_answer_relevance(self, query: str, answer: str) -> Dict[str, Any]:
        """
        Evaluates if the answer is relevant and addresses the query.
        """
        prompt = f"""Evaluate if the answer is relevant to and addresses the query.

Query: {query}

Answer: {answer}

Provide evaluation:
1. Relevance Score (0-1): [score]
2. Does it answer the query?: YES/NO
3. Reasoning: [explanation]
"""
        
        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        # Extract score
        score = 0.0
        if "Relevance Score" in content:
            try:
                score_line = [l for l in content.split('\n') if 'Relevance Score' in l][0]
                score = float(score_line.split(':')[1].strip().split()[0])
            except:
                score = 0.5
        
        answers_query = "YES" in content
        verdict = "RELEVANT" if score >= 0.7 else "IRRELEVANT"
        
        return {
            "metric": "answer_relevance",
            "score": score,
            "answers_query": answers_query,
            "evaluation": content,
            "verdict": verdict
        }
    
    def evaluate_noise_robustness(self, query: str, answer: str, 
                                   relevant_contexts: List[str], 
                                   noise_contexts: List[str]) -> Dict[str, Any]:
        """
        Evaluates if the system can handle irrelevant/noisy contexts.
        Tests if the answer focuses on relevant info and ignores noise.
        """
        prompt = f"""Evaluate if the answer correctly focuses on relevant information 
and ignores irrelevant noise.

Query: {query}

Relevant Contexts:
{chr(10).join([f"- {ctx}" for ctx in relevant_contexts])}

Noise (Irrelevant) Contexts:
{chr(10).join([f"- {ctx}" for ctx in noise_contexts])}

Answer: {answer}

Evaluate:
1. Noise Robustness Score (0-1): [score]
2. Does answer use mainly relevant contexts?: YES/NO
3. Does answer reference noise?: YES/NO
4. Reasoning: [explanation]
"""
        
        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        score = 0.0
        if "Noise Robustness Score" in content:
            try:
                score_line = [l for l in content.split('\n') if 'Noise Robustness Score' in l][0]
                score = float(score_line.split(':')[1].strip().split()[0])
            except:
                score = 0.5
        
        verdict = "ROBUST" if score >= 0.7 else "NOT_ROBUST"
        
        return {
            "metric": "noise_robustness",
            "score": score,
            "evaluation": content,
            "verdict": verdict
        }
    
    def comprehensive_evaluation(self, query: str, answer: str, 
                                 contexts: List[str], 
                                 sources: List[Dict]) -> Dict[str, Any]:
        """
        Runs all evaluation metrics and provides a comprehensive report.
        """
        # Extract context text from documents
        context_texts = [ctx[:500] for ctx in contexts]  # Limit context length for evaluation
        
        # Run evaluations
        context_rel = self.evaluate_context_relevance(query, context_texts)
        faithfulness = self.evaluate_faithfulness(answer, context_texts)
        answer_rel = self.evaluate_answer_relevance(query, answer)
        
        # Calculate overall score
        overall_score = (
            context_rel["score"] * 0.3 +
            faithfulness["score"] * 0.4 +
            answer_rel["score"] * 0.3
        )
        
        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "metrics": {
                "context_relevance": context_rel,
                "faithfulness": faithfulness,
                "answer_relevance": answer_rel
            },
            "overall_score": round(overall_score, 3),
            "overall_verdict": "PASS" if overall_score >= 0.7 else "FAIL",
            "recommendations": self._generate_recommendations(
                context_rel, faithfulness, answer_rel
            )
        }
    
    def _generate_recommendations(self, context_rel: Dict, 
                                 faithfulness: Dict, 
                                 answer_rel: Dict) -> List[str]:
        """Generate actionable recommendations based on evaluation results."""
        recommendations = []
        
        if context_rel["score"] < 0.7:
            recommendations.append(
                "⚠️ Low context relevance - Consider adjusting chunk size or Top K parameter"
            )
        
        if faithfulness["score"] < 0.8:
            recommendations.append(
                "⚠️ Low faithfulness - Reduce temperature or improve prompt instructions"
            )
        
        if answer_rel["score"] < 0.7:
            recommendations.append(
                "⚠️ Low answer relevance - Review query or improve context retrieval"
            )
        
        if not recommendations:
            recommendations.append("✅ All metrics performing well!")
        
        return recommendations
