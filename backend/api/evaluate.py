from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging

from backend.evaluators.alignment import RetrievalGenerationAlignmentEvaluator
from backend.evaluators.citation import CitationAccuracyEvaluator
from backend.evaluators.contradiction import ContextContradictionDetector
from backend.services.monitoring import RAGMonitor
from backend.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])

_alignment_eval = None
_citation_eval = None
_contradiction_eval = None


def get_alignment_evaluator():
    global _alignment_eval
    if _alignment_eval is None:
        _alignment_eval = RetrievalGenerationAlignmentEvaluator()
    return _alignment_eval


def get_citation_evaluator():
    global _citation_eval
    if _citation_eval is None:
        _citation_eval = CitationAccuracyEvaluator()
    return _citation_eval


def get_contradiction_evaluator():
    global _contradiction_eval
    if _contradiction_eval is None:
        _contradiction_eval = ContextContradictionDetector()
    return _contradiction_eval


class EvaluationRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    retrieved_docs: List[str] = Field(..., min_length=1)
    answer: str = Field(..., min_length=1, max_length=50000)
    doc_urls: Optional[List[str]] = []


class EvaluationResponse(BaseModel):
    alignment_score: Optional[float] = None
    citation_accuracy: float
    contradiction_score: float
    overall_score: Optional[float] = None
    issues: List[str]
    details: dict


class BatchEvaluationRequest(BaseModel):
    evaluations: List[EvaluationRequest]


class BatchEvaluationResponse(BaseModel):
    total: int
    passed: int
    passed_percentage: float
    average_overall: float
    average_alignment: float
    average_citation: float
    average_contradiction: float
    results: List[dict]
    issues_summary: dict


@router.post("/rag", response_model=EvaluationResponse)
async def evaluate_rag(req: EvaluationRequest, db: Session = Depends(get_db)):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Set it in your .env file.",
        )

    retrieved_docs = [d.strip() for d in req.retrieved_docs if d.strip()]
    if not retrieved_docs:
        raise HTTPException(status_code=422, detail="At least one non-empty retrieved document is required.")

    try:
        alignment_eval = get_alignment_evaluator()
        alignment_result = await alignment_eval.evaluate(req.query, retrieved_docs, req.answer)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Alignment evaluation failed")
        raise HTTPException(status_code=502, detail=f"Alignment evaluation failed: {e}")

    citation_eval = get_citation_evaluator()
    citation_result = citation_eval.evaluate(req.answer, retrieved_docs)

    try:
        contradiction_eval = get_contradiction_evaluator()
        contradiction_result = await contradiction_eval.evaluate(req.answer, retrieved_docs)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Contradiction evaluation failed")
        raise HTTPException(status_code=502, detail=f"Contradiction evaluation failed: {e}")

    alignment_score = alignment_result.get('alignment_score')
    citation_score = citation_result.get('citation_accuracy', 0.0)
    contradiction_score = contradiction_result.get('contradiction_score', 0.0)

    issues = []

    if alignment_result.get('parse_error'):
        issues.append("Alignment evaluation could not be parsed — score unavailable.")
        alignment_score = None
    elif alignment_score is not None and alignment_score < 0.6:
        issues.append("Answer doesn't use most retrieved documents.")

    if citation_score < 0.8 and citation_result.get('total_citations', 0) > 0:
        issues.append("Citations may be inaccurate or hallucinated.")

    if contradiction_score < 0.5:
        issues.append("Answer contradicts its own sources.")

    scores_for_overall = []
    weights = []
    if alignment_score is not None:
        scores_for_overall.append(alignment_score)
        weights.append(0.30)
    scores_for_overall.append(citation_score)
    weights.append(0.35)
    scores_for_overall.append(contradiction_score)
    weights.append(0.35)

    total_weight = sum(weights)
    overall = sum(s * w for s, w in zip(scores_for_overall, weights)) / total_weight

    # Store None for alignment_score if unavailable — avoids biasing monitoring averages
    response_data = {
        "overall_score": overall,
        "alignment_score": alignment_score,  # may be None — monitored correctly
        "citation_accuracy": citation_score,
        "contradiction_score": contradiction_score,
        "query": req.query,
        "answer": req.answer,
    }

    try:
        monitor = RAGMonitor(db)
        monitor.log_evaluation(response_data)
    except Exception as e:
        logger.warning("Failed to log evaluation to monitoring: %s", e)

    return EvaluationResponse(
        alignment_score=alignment_score,
        citation_accuracy=citation_score,
        contradiction_score=contradiction_score,
        overall_score=overall,
        issues=issues,
        details={
            "alignment": alignment_result,
            "citation": citation_result,
            "contradiction": contradiction_result,
            "doc_urls": req.doc_urls or [],
        },
    )


@router.get("/monitoring")
async def get_monitoring_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    if hours < 1 or hours > 720:
        raise HTTPException(status_code=422, detail="hours must be between 1 and 720")

    monitor = RAGMonitor(db)
    return monitor.get_metrics(hours)


@router.post("/batch", response_model=BatchEvaluationResponse)
async def batch_evaluate(req: BatchEvaluationRequest, db: Session = Depends(get_db)):
    """
    Run multiple evaluations and return aggregated statistics.
    """
    all_results = []
    passed_count = 0
    total_scores = {"overall": 0, "alignment": 0, "citation": 0, "contradiction": 0}
    issues_counter = {}

    for item in req.evaluations:
        try:
            # Run evaluators
            alignment_eval = get_alignment_evaluator()
            alignment_result = await alignment_eval.evaluate(
                item.query, item.retrieved_docs, item.answer
            )

            citation_eval = get_citation_evaluator()
            citation_result = citation_eval.evaluate(
                item.answer, item.retrieved_docs
            )

            contradiction_eval = get_contradiction_evaluator()
            contradiction_result = await contradiction_eval.evaluate(
                item.answer, item.retrieved_docs
            )

            alignment_score = alignment_result.get('alignment_score')
            if alignment_score is None:
                alignment_score = 0.0
            
            citation_score = citation_result.get('citation_accuracy', 0.0)
            contradiction_score = contradiction_result.get('contradiction_score', 0.0)

            overall = (
                alignment_score * 0.30 +
                citation_score * 0.35 +
                contradiction_score * 0.35
            )

            # Track issues
            issues = []
            if alignment_score < 0.6:
                issues.append("Answer doesn't use most retrieved documents")
            if citation_score < 0.8:
                issues.append("Citations may be inaccurate or hallucinated")
            if contradiction_score < 0.5:
                issues.append("Answer contradicts its sources")

            # Count issues
            for issue in issues:
                issues_counter[issue] = issues_counter.get(issue, 0) + 1

            # Track pass/fail (overall >= 0.7 = pass)
            if overall >= 0.7:
                passed_count += 1

            total_scores["overall"] += overall
            total_scores["alignment"] += alignment_score
            total_scores["citation"] += citation_score
            total_scores["contradiction"] += contradiction_score

            # Store in database
            monitor = RAGMonitor(db)
            monitor.log_evaluation({
                "overall_score": overall,
                "alignment_score": alignment_score,
                "citation_accuracy": citation_score,
                "contradiction_score": contradiction_score,
                "query": item.query,
                "answer": item.answer
            })

            all_results.append({
                "query": item.query,
                "overall_score": overall,
                "alignment_score": alignment_score,
                "citation_accuracy": citation_score,
                "contradiction_score": contradiction_score,
                "passed": overall >= 0.7,
                "issues": issues
            })

        except Exception as e:
            all_results.append({
                "query": item.query,
                "error": str(e)
            })

    n = len(req.evaluations)
    if n > 0:
        avg_overall = total_scores["overall"] / n
        avg_alignment = total_scores["alignment"] / n
        avg_citation = total_scores["citation"] / n
        avg_contradiction = total_scores["contradiction"] / n
        passed_pct = (passed_count / n) * 100
    else:
        avg_overall = avg_alignment = avg_citation = avg_contradiction = 0.0
        passed_pct = 0.0

    return BatchEvaluationResponse(
        total=n,
        passed=passed_count,
        passed_percentage=passed_pct,
        average_overall=avg_overall,
        average_alignment=avg_alignment,
        average_citation=avg_citation,
        average_contradiction=avg_contradiction,
        results=all_results,
        issues_summary=issues_counter
    )
