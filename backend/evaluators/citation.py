from typing import List, Dict, Optional, Tuple
import re


class CitationAccuracyEvaluator:
    """
    Verifies that citations actually exist in source documents.

    Extracts citations from the answer, associates quoted or contextual text
    with each citation, and verifies that text appears in the cited document.
    """

    CITATION_PATTERN = re.compile(
        r'\[(?:source\s*)?(\d+(?:\s*,\s*\d+)*)\]|'
        r'\[doc\s*(\d+)\]|'
        r'\(([^)]+et\s+al\.\s*,\s*\d{4})\)',
        re.IGNORECASE,
    )

    QUOTED_TEXT_PATTERN = re.compile(r'"([^"]+)"\s*\[(?:source\s*)?\d')

    def evaluate(self, answer: str, retrieved_docs: List[str]) -> Dict:
        citations = self._extract_citation_entries(answer)

        if not citations:
            return {
                "citation_accuracy": 1.0,
                "valid_citations": 0,
                "total_citations": 0,
                "invalid_citations": [],
                "details": "No citations found in the answer.",
            }

        valid_citations = []
        invalid_citations = []
        details = []

        for entry in citations:
            is_valid, reason = self._verify_citation_entry(entry, retrieved_docs)
            if is_valid:
                valid_citations.append(entry["raw"])
            else:
                invalid_citations.append(entry["raw"])

            details.append({
                "citation": entry["raw"],
                "refs": entry["refs"],
                "associated_text": entry["associated_text"],
                "valid": is_valid,
                "reason": reason,
            })

        total = len(citations)
        valid_count = len(valid_citations)
        citation_accuracy = valid_count / total if total > 0 else 1.0

        return {
            "citation_accuracy": citation_accuracy,
            "valid_citations": valid_count,
            "total_citations": total,
            "invalid_citations": invalid_citations,
            "details": details,
        }

    def _extract_citation_entries(self, answer: str) -> List[Dict]:
        entries = []

        for match in self.CITATION_PATTERN.finditer(answer):
            raw = match.group(0)
            start = match.start()

            if match.group(1) is not None:
                refs = [int(r.strip()) for r in match.group(1).split(",")]
            elif match.group(2) is not None:
                refs = [int(match.group(2))]
            else:
                refs = [match.group(3).strip()]

            associated_text = self._extract_associated_text(answer, start)

            entries.append({
                "raw": raw,
                "refs": refs,
                "associated_text": associated_text,
            })

        return entries

    def _extract_associated_text(self, answer: str, citation_start: int) -> str:
        text_before = answer[:citation_start].strip()

        quoted_matches = list(self.QUOTED_TEXT_PATTERN.finditer(answer[:citation_start]))
        if quoted_matches:
            return quoted_matches[-1].group(1).strip()

        sentences = re.split(r'(?<=[.!?])\s+', text_before)
        if sentences:
            last_sentence = sentences[-1].strip()
            last_sentence = re.sub(r'\[(?:source\s*)?\d+(?:\s*,\s*\d+)*\]\s*$', '', last_sentence).strip()
            if last_sentence:
                return last_sentence

        if text_before:
            lines = text_before.split('\n')
            return lines[-1].strip()

        return ""

    def _verify_citation_entry(
        self, entry: Dict, retrieved_docs: List[str]
    ) -> Tuple[bool, str]:
        refs = entry["refs"]
        associated_text = entry["associated_text"]

        if isinstance(refs[0], str):
            return self._verify_author_citation(refs[0], associated_text, retrieved_docs)

        doc_indices = []
        for ref in refs:
            if not isinstance(ref, int):
                return False, f"Invalid citation reference: {ref}"
            doc_idx = ref - 1
            if doc_idx < 0 or doc_idx >= len(retrieved_docs):
                return False, f"Reference [{ref}] points to non-existent document (have {len(retrieved_docs)} docs)"
            doc_indices.append(doc_idx)

        if not associated_text:
            return False, "No associated text found for citation — cannot verify content"

        normalized_text = self._normalize_text(associated_text)
        if len(normalized_text) < 10:
            return False, "Associated text too short to verify meaningfully"

        for doc_idx in doc_indices:
            doc_normalized = self._normalize_text(retrieved_docs[doc_idx])
            if self._text_in_document(normalized_text, doc_normalized):
                return True, f"Verified in document {doc_idx + 1}"

        return False, f"Associated text not found in cited document(s): {refs}"

    def _verify_author_citation(
        self, author_ref: str, associated_text: str, retrieved_docs: List[str]
    ) -> Tuple[bool, str]:
        author_lower = author_ref.lower()
        for i, doc in enumerate(retrieved_docs):
            if author_lower in doc.lower():
                if associated_text:
                    normalized_text = self._normalize_text(associated_text)
                    doc_normalized = self._normalize_text(doc)
                    if self._text_in_document(normalized_text, doc_normalized):
                        return True, f"Author citation verified in document {i + 1}"
                    return False, f"Author found in doc {i + 1} but associated text not verified"
                return True, f"Author citation found in document {i + 1}"
        return False, f"Author citation '{author_ref}' not found in any document"

    def _normalize_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())

    def _text_in_document(self, text: str, document: str) -> bool:
        if text in document:
            return True

        words = text.split()
        if len(words) >= 4:
            for window_size in range(len(words), 3, -1):
                for i in range(len(words) - window_size + 1):
                    phrase = ' '.join(words[i:i + window_size])
                    if phrase in document:
                        return True

        return False
