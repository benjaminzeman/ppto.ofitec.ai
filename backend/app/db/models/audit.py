from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    entity = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    data = Column(JSON)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class UserProjectRole(Base):
    __tablename__ = "user_project_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    role = Column(String)
