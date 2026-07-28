from typing import List, Dict
from langchain_groq import ChatGroq
import os
import re

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
            api_key=api_key
        )

    def evaluate(self, query: str, retrieved_docs: List[str], answer: str) -> Dict:
        """
        Score: How many retrieved documents are actually used in the answer?

        Returns:
            - alignment_score: 0-1 (1 = uses all docs, 0 = ignores all)
            - usage_map: which docs were used/unused
            - explanation: why the score was given
        """
        # Step 1: Create the prompt for the LLM
        doc_text = "\n".join([f"DOC {i}: {doc[:500]}" for i, doc in enumerate(retrieved_docs)])

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

        # Step 2: Call the LLM
        response = self.llm.invoke(prompt)
        response_text = response.content

        # Step 3: Parse the response
        usage_map = self._parse_usage(response_text)

        # Step 4: Calculate score
        used_count = sum(1 for v in usage_map.values() if v == "USED")
        total_relevant = sum(1 for v in usage_map.values() if v != "NOT_RELEVANT")

        if total_relevant == 0:
            alignment_score = 0.0  # No relevant docs available
        else:
            alignment_score = used_count / total_relevant

        return {
            "alignment_score": alignment_score,
            "usage_map": usage_map,
            "used_count": used_count,
            "total_relevant": total_relevant,
            "explanation": response_text
        }

    def _parse_usage(self, response_text: str) -> Dict[str, str]:
        """Parse LLM response to extract usage for each document."""
        usage_map = {}
        lines = response_text.strip().split('\n')

        for line in lines:
            # Match patterns like "DOC 0: USED" or "DOC 1: UNUSED"
            match = re.match(r'DOC\s+(\d+):\s+(\w+)', line.strip())
            if match:
                doc_idx = f"doc_{match.group(1)}"
                status = match.group(2).upper()
                if status in ["USED", "UNUSED", "NOT_RELEVANT"]:
                    usage_map[doc_idx] = status

        return usage_map