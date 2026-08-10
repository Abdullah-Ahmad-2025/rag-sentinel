from typing import List, Dict
from langchain_groq import ChatGroq
import os
import re

MAX_DOC_CHARS = 2000


class RetrievalGenerationAlignmentEvaluator:
    """
    Measures how well the LLM uses retrieved documents.

    Problem: RAGAS faithfulness can score 0.9 even if LLM ignores half the docs.
    This catches that.

    High score = answer incorporates most relevant context.
    Low score = answer ignores documents (dangerous!)
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=api_key,
            timeout=30,
        )

    async def evaluate(self, query: str, retrieved_docs: List[str], answer: str) -> Dict:
        if not retrieved_docs:
            return {
                "alignment_score": 1.0,
                "usage_map": {},
                "used_count": 0,
                "total_relevant": 0,
                "explanation": "No retrieved documents provided.",
                "parse_error": False,
            }

        doc_text = "\n".join([
            f"DOC {i}: {doc[:MAX_DOC_CHARS]}" for i, doc in enumerate(retrieved_docs)
        ])

        prompt = f"""You are evaluating a RAG (Retrieval-Augmented Generation) system.

Query: {query}

Retrieved documents:
{doc_text}

Generated answer:
{answer}

For each document, determine if the answer:
- DIRECTLY USES it (quotes or paraphrases it) → mark as USED
- COULD HAVE USED it but didn't → mark as UNUSED
- NOT RELEVANT to the answer → mark as NOT_RELEVANT

Respond in this exact format:
DOC 0: USED
DOC 1: UNUSED
DOC 2: NOT_RELEVANT
...

Also provide a brief explanation of your reasoning:"""

        response = await self.llm.ainvoke(prompt)
        response_text = response.content

        usage_map = self._parse_usage(response_text, len(retrieved_docs))
        parse_error = len(usage_map) == 0

        if parse_error:
            response = await self.llm.ainvoke(
                prompt + "\n\nIMPORTANT: You must respond with DOC N: STATUS lines for every document."
            )
            response_text = response.content
            usage_map = self._parse_usage(response_text, len(retrieved_docs))
            parse_error = len(usage_map) == 0

        used_count = sum(1 for v in usage_map.values() if v == "USED")
        total_relevant = sum(1 for v in usage_map.values() if v != "NOT_RELEVANT")

        if parse_error:
            alignment_score = None
        elif total_relevant == 0:
            alignment_score = 1.0
        else:
            alignment_score = used_count / total_relevant

        return {
            "alignment_score": alignment_score,
            "usage_map": usage_map,
            "used_count": used_count,
            "total_relevant": total_relevant,
            "explanation": response_text,
            "parse_error": parse_error,
        }

    def _parse_usage(self, response_text: str, expected_docs: int) -> Dict[str, str]:
        usage_map = {}
        lines = response_text.strip().split('\n')

        for line in lines:
            match = re.match(r'DOC\s+(\d+):\s+(\w+)', line.strip())
            if match:
                doc_idx = f"doc_{match.group(1)}"
                status = match.group(2).upper()
                if status in ["USED", "UNUSED", "NOT_RELEVANT"]:
                    usage_map[doc_idx] = status

        for i in range(expected_docs):
            key = f"doc_{i}"
            if key not in usage_map:
                usage_map[key] = "UNUSED"

        return usage_map
