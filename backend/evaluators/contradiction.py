from typing import List, Dict
from langchain_groq import ChatGroq
import os
import re

class ContextContradictionDetector:
    """
    Detect if answer contradicts its own sources.

    Example: Answer says "X is green" but retrieved doc says "X is blue"

    Returns:
        - contradiction_score: 0.0 = severe contradiction, 1.0 = no contradiction
        - has_contradiction: boolean
        - explanation: reasoning from the LLM judge
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",  # Use the latest recommended model
            temperature=0,
            api_key=api_key
        )

    def evaluate(self, answer: str, retrieved_docs: List[str]) -> Dict:
        """
        Check for internal contradictions between answer and sources.
        """
        # Prepare documents (truncate to avoid token limits)
        doc_text = "\n".join([f"SOURCE {i}: {doc[:500]}" for i, doc in enumerate(retrieved_docs)])

        prompt = f"""
You are evaluating a RAG (Retrieval-Augmented Generation) system.

Answer to evaluate:
{answer}

Source documents:
{doc_text}

Your task:
Does the answer contradict any of its sources?

- If the answer directly contradicts any source → "YES"
- If the answer is consistent but has minor inconsistencies → "PARTIAL"
- If the answer is fully consistent with all sources → "NO"

Respond in this exact format:
VERDICT: [YES/PARTIAL/NO]
DETAILS: [explanation of why]
SPECIFIC_CONTRADICTIONS: [list any specific contradictions found]
"""

        response = self.llm.invoke(prompt)
        response_text = response.content

        # Parse the response
        verdict, explanation, specifics = self._parse_response(response_text)

        # Convert verdict to score
        if "yes" in verdict.lower():
            contradiction_score = 0.0
            has_contradiction = True
        elif "partial" in verdict.lower():
            contradiction_score = 0.5
            has_contradiction = True
        else:
            contradiction_score = 1.0
            has_contradiction = False

        return {
            "contradiction_score": contradiction_score,
            "has_contradiction": has_contradiction,
            "verdict": verdict,
            "explanation": explanation,
            "specific_contradictions": specifics
        }

    def _parse_response(self, response_text: str) -> tuple:
        """Parse the LLM response to extract verdict, explanation, and specifics."""
        verdict = "NO"
        explanation = "No contradictions detected."
        specifics = []

        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith("VERDICT:"):
                verdict = line.replace("VERDICT:", "").strip()
            elif line.startswith("DETAILS:"):
                explanation = line.replace("DETAILS:", "").strip()
            elif line.startswith("SPECIFIC_CONTRADICTIONS:"):
                # The rest might contain list of contradictions
                specifics = [l.strip() for l in lines[lines.index(line)+1:] if l.strip()]

        return verdict, explanation, specifics