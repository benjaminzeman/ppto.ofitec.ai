from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Text
from app.db.base import Base

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    source = Column(String, default="manual")
    qty = Column(Numeric(16,3), default=0)
    note = Column(Text)
