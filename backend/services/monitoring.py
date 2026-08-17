from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List

from backend.models.schema import EvaluationLog, MonitoringAlert


def _utcnow():
    return datetime.now(timezone.utc)


class RAGMonitor:
    """
    Monitor RAG quality in production.
    Tracks scores over time and alerts on quality drops.
    """

    def __init__(self, db: Session):
        self.db = db
        self.threshold = 0.65

    def log_evaluation(self, evaluation_result: dict) -> None:
        log = EvaluationLog(
            timestamp=_utcnow(),
            session_id=evaluation_result.get('session_id'),
            overall_score=evaluation_result.get('overall_score', 0.0),
            # Store None if alignment was unavailable — avoids biasing avg_score
            alignment_score=evaluation_result.get('alignment_score'),
            citation_accuracy=evaluation_result.get('citation_accuracy', 0.0),
            contradiction_score=evaluation_result.get('contradiction_score', 0.0),
            query=evaluation_result.get('query', ''),
            answer=evaluation_result.get('answer', '')
        )
        self.db.add(log)
        self.db.commit()
        self._check_for_alerts()

    def _check_for_alerts(self) -> None:
        day_ago = _utcnow() - timedelta(days=1)
        recent = self.db.query(EvaluationLog).filter(
            EvaluationLog.timestamp > day_ago
        ).all()

        if not recent:
            return

        avg_score = sum(e.overall_score for e in recent) / len(recent)

        if avg_score >= self.threshold:
            return

        hour_ago = _utcnow() - timedelta(hours=1)
        existing = self.db.query(MonitoringAlert).filter(
            MonitoringAlert.alert_type == "quality_drop",
            MonitoringAlert.timestamp > hour_ago,
        ).first()

        if existing:
            return

        alert = MonitoringAlert(
            timestamp=_utcnow(),
            alert_type="quality_drop",
            message=f"RAG quality dropped to {avg_score:.2f} in the last 24 hours",
            severity="high" if avg_score < 0.5 else "medium",
            avg_score=avg_score,
            threshold=self.threshold,
        )
        self.db.add(alert)
        self.db.commit()

    def get_metrics(self, hours: int = 24, session_id: str = None) -> dict:
        cutoff = _utcnow() - timedelta(hours=hours)

        query = self.db.query(EvaluationLog).filter(
            EvaluationLog.timestamp > cutoff
        )

        # Filter by session if provided
        if session_id:
            query = query.filter(EvaluationLog.session_id == session_id)

        logs = query.order_by(EvaluationLog.timestamp.asc()).all()

        alert_count = len(
            self.db.query(MonitoringAlert).filter(
                MonitoringAlert.timestamp > cutoff
            ).all()
        )

        # Always return a consistent shape — no_data flag instead of error string
        if not logs:
            return {
                "no_data": True,
                "total_evaluations": 0,
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "trend": "stable",
                "alert_count": alert_count,
                "recent_evaluations": [],
            }

        return {
            "no_data": False,
            "avg_score": sum(e.overall_score for e in logs) / len(logs),
            "min_score": min(e.overall_score for e in logs),
            "max_score": max(e.overall_score for e in logs),
            "total_evaluations": len(logs),
            "trend": self._calculate_trend(logs),
            "alert_count": alert_count,
            # Last 20 evaluations for the history table + trend chart
            "recent_evaluations": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "overall_score": e.overall_score,
                    "alignment_score": e.alignment_score,
                    "citation_accuracy": e.citation_accuracy,
                    "contradiction_score": e.contradiction_score,
                    "query": (e.query or "")[:120],
                }
                for e in logs[-20:]
            ],
        }

    def _calculate_trend(self, logs: List[EvaluationLog]) -> str:
        if len(logs) < 2:
            return "stable"

        mid = len(logs) // 2
        first_half = [e.overall_score for e in logs[:mid]]
        second_half = [e.overall_score for e in logs[mid:]]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        diff = second_avg - first_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "degrading"
        else:
            return "stable"
