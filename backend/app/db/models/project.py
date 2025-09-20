from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    currency = Column(String, default="CLP")
    baseline_version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="SET NULL"), nullable=True)
