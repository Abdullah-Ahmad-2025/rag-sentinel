from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.evaluators.alignment import RetrievalGenerationAlignmentEvaluator
from backend.evaluators.citation import CitationAccuracyEvaluator
from backend.evaluators.contradiction import ContextContradictionDetector

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])

# ---- Request/Response Models ----
class EvaluationRequest(BaseModel):
    query: str
    retrieved_docs: List[str]
    answer: str
    doc_urls: Optional[List[str]] = []  # optional source tracking

class EvaluationResponse(BaseModel):
    alignment_score: float
    citation_accuracy: float
    contradiction_score: float
    overall_score: float
    issues: List[str]
    details: dict  # raw outputs from each evaluator

# ---- Endpoint ----
@router.post("/rag", response_model=EvaluationResponse)
async def evaluate_rag(req: EvaluationRequest):
    """
    Comprehensive RAG evaluation using three custom metrics.
    """
    # 1. Alignment Evaluator
    alignment_eval = RetrievalGenerationAlignmentEvaluator()
    alignment_result = alignment_eval.evaluate(
        req.query, req.retrieved_docs, req.answer
    )

    # 2. Citation Accuracy Evaluator
    citation_eval = CitationAccuracyEvaluator()
    citation_result = citation_eval.evaluate(
        req.answer, req.retrieved_docs
    )

    # 3. Context Contradiction Evaluator
    contradiction_eval = ContextContradictionDetector()
    contradiction_result = contradiction_eval.evaluate(
        req.answer, req.retrieved_docs
    )

    # --- Aggregate scores ---
    alignment_score = alignment_result.get('alignment_score', 0.0)
    citation_score = citation_result.get('citation_accuracy', 0.0)
    contradiction_score = contradiction_result.get('contradiction_score', 0.0)

    # Weighted overall score (you can adjust weights)
    overall = (
        alignment_score * 0.30 +
        citation_score * 0.35 +
        contradiction_score * 0.35
    )

    # --- Generate issues list ---
    issues = []
    if alignment_score < 0.6:
        issues.append("Answer doesn't use most retrieved documents.")
    if citation_score < 0.8:
        issues.append("Citations may be inaccurate or hallucinated.")
    if contradiction_score < 0.5:
        issues.append("Answer contradicts its own sources.")

    # --- Build response ---
    return EvaluationResponse(
        alignment_score=alignment_score,
        citation_accuracy=citation_score,
        contradiction_score=contradiction_score,
        overall_score=overall,
        issues=issues,
        details={
            "alignment": alignment_result,
            "citation": citation_result,
            "contradiction": contradiction_result
        }
    )