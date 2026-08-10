from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=_utcnow)
    overall_score = Column(Float)
    alignment_score = Column(Float)
    citation_accuracy = Column(Float)
    contradiction_score = Column(Float)
    query = Column(Text)
    answer = Column(Text)


class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=_utcnow)
    alert_type = Column(String)
    message = Column(Text)
    severity = Column(String)
    avg_score = Column(Float)
    threshold = Column(Float)
