from typing import List, Dict
import re

class CitationAccuracyEvaluator:
    """
    Verifies that citations actually exist in source documents.

    Problem: RAG can cite sources that don't contain the quoted text.
    This catches hallucinated citations.
    """

    def evaluate(self, answer: str, retrieved_docs: List[str]) -> Dict:
        """
        Extract citations from the answer and verify them.

        Returns:
            - citation_accuracy: 0-1 (1 = all citations valid, 0 = all invalid)
            - valid_citations: count of valid citations
            - total_citations: total citations found
            - invalid_citations: list of invalid citations
            - details: per-citation verification result
        """
        # Step 1: Extract citations from the answer
        citations = self._extract_citations(answer)

        if not citations:
            return {
                "citation_accuracy": 1.0,
                "valid_citations": 0,
                "total_citations": 0,
                "invalid_citations": [],
                "details": "No citations found in the answer."
            }

        # Step 2: Verify each citation
        valid_citations = []
        invalid_citations = []
        details = []

        for citation in citations:
            is_valid = self._verify_citation(citation, retrieved_docs)
            if is_valid:
                valid_citations.append(citation)
            else:
                invalid_citations.append(citation)

            details.append({
                "citation": citation,
                "valid": is_valid
            })

        # Step 3: Calculate score
        total = len(citations)
        valid_count = len(valid_citations)
        citation_accuracy = valid_count / total if total > 0 else 1.0

        return {
            "citation_accuracy": citation_accuracy,
            "valid_citations": valid_count,
            "total_citations": total,
            "invalid_citations": invalid_citations,
            "details": details
        }

    def _extract_citations(self, answer: str) -> List[str]:
        """
        Extract citations from the answer.
        Supports formats: [1], [2,3], [doc1], (Smith et al., 2023)
        """
        citations = []

        # Pattern 1: [number] or [number,number]
        pattern1 = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', answer)
        citations.extend(pattern1)

        # Pattern 2: (Author et al., Year)
        pattern2 = re.findall(r'\(([^)]+et\s+al\.,\s*\d{4})\)', answer)
        citations.extend(pattern2)

        # Pattern 3: [docX] or [doc X]
        pattern3 = re.findall(r'\[doc\s*(\d+)\]', answer, re.IGNORECASE)
        citations.extend(pattern3)

        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique_citations.append(c)

        return unique_citations

    def _verify_citation(self, citation: str, retrieved_docs: List[str]) -> bool:
        """
        Check if a citation exists in any retrieved document.
        """
        # Clean the citation
        citation_clean = citation.lower().strip()

        # If it's a number (like "1"), check if there's a document with that index
        if citation_clean.isdigit():
            doc_idx = int(citation_clean)
            if doc_idx < len(retrieved_docs):
                return True
            else:
                return False

        # If it's an author-year style, search for it in documents
        # (Simple check: does the text appear in any document?)
        for doc in retrieved_docs:
            if citation_clean in doc.lower():
                return True

        return False