from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, text
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # server_default para alinearse con migración (boolean literal)
    is_active = Column(Boolean, default=True, server_default=text('true'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
