from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func
from app.db.base import Base

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    code = Column(String, index=True)
    name = Column(String)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    code = Column(String, index=True)
    name = Column(String)
    unit = Column(String, default="m2")
    quantity = Column(Numeric(16,3), default=0)
    price = Column(Numeric(16,2), default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    type = Column(String)
    code = Column(String, index=True)
    name = Column(String)
    unit = Column(String, default="u")
    unit_cost = Column(Numeric(16,4), default=0)

class APU(Base):
    __tablename__ = "apus"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="RESTRICT"))
    coeff = Column(Numeric(16,6), default=0)


class MeasurementBatch(Base):
    __tablename__ = "measurement_batches"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String)
    status = Column(String, default="open")  # open, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MeasurementLine(Base):
    __tablename__ = "measurement_lines"
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("measurement_batches.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    qty = Column(Numeric(16,3), default=0)
