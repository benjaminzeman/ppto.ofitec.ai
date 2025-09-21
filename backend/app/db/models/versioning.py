from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, Text, func, Boolean
from app.db.base import Base
from sqlalchemy import Date, JSON

class BudgetVersion(Base):
    __tablename__ = "budget_versions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_baseline = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)

class BudgetVersionItem(Base):
    __tablename__ = "budget_version_items"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), index=True)
    chapter_code = Column(String, index=True)
    chapter_name = Column(String)
    item_code = Column(String)
    item_name = Column(String)
    unit = Column(String)
    qty = Column(Numeric(16,3))
    unit_price = Column(Numeric(16,2))


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # e.g. 'version', 'purchase_order'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    position = Column(Integer, nullable=False)
    role_required = Column(String, nullable=False)  # admin/editor/approver custom
    name = Column(String, nullable=False)


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    status = Column(String, default="running")  # running, approved, rejected
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    current_step = Column(Integer, default=1)


class WorkflowInstanceStep(Base):
    __tablename__ = "workflow_instance_steps"
    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id", ondelete="CASCADE"), index=True)
    step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete="CASCADE"), index=True)
    position = Column(Integer, nullable=False)
    decision = Column(String, nullable=True)  # approved/rejected
    decided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime(timezone=True))
    comment = Column(Text)


# --- Facturación & Banco (Sprint 11-12) ---

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    dte_number = Column(String, index=True)
    status = Column(String, default="pending")  # pending|accepted|rejected|paid
    amount = Column(Numeric(16,2))
    currency = Column(String, default="CLP")
    xml_ref = Column(String)  # path o hash del XML
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True))

class InvoicePayment(Base):
    __tablename__ = "invoice_payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    amount = Column(Numeric(16,2))
    method = Column(String)  # transfer|cash|other
    reference = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    date = Column(Date, index=True)
    description = Column(String)
    amount = Column(Numeric(16,2))
    balance = Column(Numeric(16,2))
    source = Column(String)  # banco_chile|santander|manual
    raw = Column(JSON)
    matched_invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)

git config --global user.name "Tu Nombre"
git config --global user.email "tu_email@dominio.com"
