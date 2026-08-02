from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid

from backend.evaluators.alignment import RetrievalGenerationAlignmentEvaluator
from backend.evaluators.citation import CitationAccuracyEvaluator
from backend.evaluators.contradiction import ContextContradictionDetector
from backend.services.monitoring import RAGMonitor
from backend.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])

class EvaluationRequest(BaseModel):
    query: str
    retrieved_docs: List[str]
    answer: str
    doc_urls: Optional[List[str]] = []

class EvaluationResponse(BaseModel):
    alignment_score: float
    citation_accuracy: float
    contradiction_score: float
    overall_score: float
    issues: List[str]
    details: dict

@router.post("/rag", response_model=EvaluationResponse)
async def evaluate_rag(req: EvaluationRequest, db: Session = Depends(get_db)):
    # Run evaluators...
    alignment_eval = RetrievalGenerationAlignmentEvaluator()
    alignment_result = alignment_eval.evaluate(
        req.query, req.retrieved_docs, req.answer
    )

    citation_eval = CitationAccuracyEvaluator()
    citation_result = citation_eval.evaluate(
        req.answer, req.retrieved_docs
    )

    contradiction_eval = ContextContradictionDetector()
    contradiction_result = contradiction_eval.evaluate(
        req.answer, req.retrieved_docs
    )

    alignment_score = alignment_result.get('alignment_score', 0.0)
    citation_score = citation_result.get('citation_accuracy', 0.0)
    contradiction_score = contradiction_result.get('contradiction_score', 0.0)

    overall = (
        alignment_score * 0.30 +
        citation_score * 0.35 +
        contradiction_score * 0.35
    )

    issues = []
    if alignment_score < 0.6:
        issues.append("Answer doesn't use most retrieved documents.")
    if citation_score < 0.8:
        issues.append("Citations may be inaccurate or hallucinated.")
    if contradiction_score < 0.5:
        issues.append("Answer contradicts its own sources.")

    # --- NEW: Log to monitoring ---
    monitor = RAGMonitor(db)
    monitor.log_evaluation({
        "overall_score": overall,
        "alignment_score": alignment_score,
        "citation_accuracy": citation_score,
        "contradiction_score": contradiction_score,
        "query": req.query,
        "answer": req.answer
    })

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

@router.get("/monitoring")
async def get_monitoring_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get monitoring metrics for the last N hours."""
    monitor = RAGMonitor(db)
    return monitor.get_metrics(hours)