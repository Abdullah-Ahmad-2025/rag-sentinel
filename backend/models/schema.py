from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    overall_score = Column(Float)
    alignment_score = Column(Float)
    citation_accuracy = Column(Float)
    contradiction_score = Column(Float)
    query = Column(Text)
    answer = Column(Text)

class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String)  # quality_drop, drift_detected, etc.
    message = Column(Text)
    severity = Column(String)  # low, medium, high
    avg_score = Column(Float)
    threshold = Column(Float)