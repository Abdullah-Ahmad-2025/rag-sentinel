from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict

# We'll create these models in the next step
from backend.models.schema import EvaluationLog, MonitoringAlert

class RAGMonitor:
    """
    Monitor RAG quality in production.
    Tracks scores over time and alerts on quality drops.
    """

    def __init__(self, db: Session):
        self.db = db
        self.threshold = 0.65  # Alert if overall score drops below this

    def log_evaluation(self, evaluation_result: dict) -> None:
        """
        Store evaluation in database.
        This gets called every time a user evaluates a RAG system.
        """
        log = EvaluationLog(
            timestamp=datetime.utcnow(),
            overall_score=evaluation_result.get('overall_score', 0.0),
            alignment_score=evaluation_result.get('alignment_score', 0.0),
            citation_accuracy=evaluation_result.get('citation_accuracy', 0.0),
            contradiction_score=evaluation_result.get('contradiction_score', 0.0),
            query=evaluation_result.get('query', ''),
            answer=evaluation_result.get('answer', '')
        )
        self.db.add(log)
        self.db.commit()

        # Check for alerts after logging
        self._check_for_alerts()

    def _check_for_alerts(self) -> None:
        """Detect quality drops in the last 24 hours."""
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent = self.db.query(EvaluationLog).filter(
            EvaluationLog.timestamp > day_ago
        ).all()

        if not recent:
            return

        avg_score = sum(e.overall_score for e in recent) / len(recent)

        if avg_score < self.threshold:
            # Create alert
            alert = MonitoringAlert(
                timestamp=datetime.utcnow(),
                alert_type="quality_drop",
                message=f"RAG quality dropped to {avg_score:.2f} in the last 24 hours",
                severity="high" if avg_score < 0.5 else "medium",
                avg_score=avg_score,
                threshold=self.threshold
            )
            self.db.add(alert)
            self.db.commit()

    def get_metrics(self, hours: int = 24) -> dict:
        """Get monitoring dashboard metrics for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        logs = self.db.query(EvaluationLog).filter(
            EvaluationLog.timestamp > cutoff
        ).all()

        if not logs:
            return {"error": "No data available for the selected time range"}

        return {
            "avg_score": sum(e.overall_score for e in logs) / len(logs),
            "min_score": min(e.overall_score for e in logs),
            "max_score": max(e.overall_score for e in logs),
            "total_evaluations": len(logs),
            "trend": self._calculate_trend(logs),
            "alert_count": len(
                self.db.query(MonitoringAlert).filter(
                    MonitoringAlert.timestamp > cutoff
                ).all()
            )
        }

    def _calculate_trend(self, logs: List[EvaluationLog]) -> str:
        """Determine if quality is improving, stable, or degrading."""
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