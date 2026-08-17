from typing import List, Dict, Tuple
from langchain_groq import ChatGroq
import os
import re

MAX_DOC_CHARS = 2000


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
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=api_key,
            timeout=30,
        )

    def evaluate(self, answer: str, retrieved_docs: List[str]) -> Dict:
        if not retrieved_docs:
            return {
                "contradiction_score": 1.0,
                "has_contradiction": False,
                "verdict": "NO",
                "explanation": "No retrieved documents to compare against.",
                "specific_contradictions": [],
            }

        doc_text = "\n".join([
            f"SOURCE {i}: {doc[:MAX_DOC_CHARS]}" for i, doc in enumerate(retrieved_docs)
        ])

        prompt = f"""You are evaluating a RAG (Retrieval-Augmented Generation) system.

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
SPECIFIC_CONTRADICTIONS: [list any specific contradictions found, or "None"]"""

        response = self.llm.invoke(prompt)
        response_text = response.content

        verdict, explanation, specifics = self._parse_response(response_text)

        verdict_upper = verdict.upper().strip()
        if verdict_upper == "YES":
            contradiction_score = 0.0
            has_contradiction = True
        elif verdict_upper == "PARTIAL":
            contradiction_score = 0.5
            has_contradiction = True
        else:
            contradiction_score = 1.0
            has_contradiction = False

        return {
            "contradiction_score": contradiction_score,
            "has_contradiction": has_contradiction,
            "verdict": verdict_upper,
            "explanation": explanation,
            "specific_contradictions": specifics,
        }

    def _parse_response(self, response_text: str) -> Tuple[str, str, List[str]]:
        verdict = "NO"
        explanation = "No contradictions detected."
        specifics = []

        lines = response_text.strip().split('\n')
        in_contradictions = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("VERDICT:"):
                verdict = stripped.replace("VERDICT:", "").strip()
                in_contradictions = False
            elif stripped.startswith("DETAILS:"):
                explanation = stripped.replace("DETAILS:", "").strip()
                in_contradictions = False
            elif stripped.startswith("SPECIFIC_CONTRADICTIONS:"):
                content = stripped.replace("SPECIFIC_CONTRADICTIONS:", "").strip()
                if content and content.lower() not in ("none", "n/a", "-"):
                    specifics.append(content)
                in_contradictions = True
            elif in_contradictions and stripped:
                if stripped.startswith("- "):
                    specifics.append(stripped[2:])
                elif stripped.lower() not in ("none", "n/a"):
                    specifics.append(stripped)

        return verdict, explanation, specifics
