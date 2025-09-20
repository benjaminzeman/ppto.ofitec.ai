from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, Text
from app.db.base import Base

class BudgetVersion(Base):
    __tablename__ = "budget_versions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime)

class BudgetVersionItem(Base):
    __tablename__ = "budget_version_items"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), index=True)
    item_code = Column(String)
    item_name = Column(String)
    unit = Column(String)
    qty = Column(Numeric(16,3))
    unit_price = Column(Numeric(16,2))
