from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    rq_id = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=False)  # e.g., import_excel, import_bc3, export_budget
    status = Column(String, nullable=False, default="queued")  # queued, started, finished, failed
    params = Column(Text, nullable=True)
    result_path = Column(String, nullable=True)  # path a archivo generado (export)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
