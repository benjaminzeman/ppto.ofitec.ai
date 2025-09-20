from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    currency = Column(String, default="CLP")
