from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, func
from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tax_id = Column(String, index=True)
    contact_email = Column(String)


class RFQ(Base):  # Request For Quotation
    __tablename__ = "rfqs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RFQItem(Base):
    __tablename__ = "rfq_items"
    id = Column(Integer, primary_key=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    qty = Column(Numeric(16,3), default=0)


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id = Column(Integer, primary_key=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    rfq_item_id = Column(Integer, ForeignKey("rfq_items.id", ondelete="CASCADE"), index=True)
    unit_price = Column(Numeric(16,4), default=0)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="created")  # created, approved, received, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    qty = Column(Numeric(16,3), default=0)
    unit_price = Column(Numeric(16,4), default=0)
