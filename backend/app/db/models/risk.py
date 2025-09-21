from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from app.db.base import Base

class Risk(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    category = Column(String)  # financiero|plazo|tecnico|contratos
    description = Column(Text)
    probability = Column(Integer)  # 1-5
    impact = Column(Integer)       # 1-5
    status = Column(String, default="open")  # open|mitigating|closed
    mitigation = Column(Text)
    owner = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())