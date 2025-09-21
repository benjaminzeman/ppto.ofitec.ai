from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict
from app.db.models.versioning import Invoice, InvoicePayment, BankTransaction
from datetime import date
from app.services.audit import log_action


def create_invoice(db: Session, user_id: int, project_id: int, amount: float, currency: str = "CLP", dte_number: str | None = None) -> Invoice:
    inv = Invoice(project_id=project_id, amount=amount, currency=currency, dte_number=dte_number)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log_action(db, project_id=project_id, entity="invoice", entity_id=inv.id, action="invoice_create", data={"amount": str(amount)}, user_id=user_id)
    return inv


def list_invoices(db: Session, project_id: int) -> List[Invoice]:
    return db.query(Invoice).filter(Invoice.project_id == project_id).order_by(Invoice.id.desc()).all()


def send_sii(db: Session, user_id: int, inv: Invoice) -> Invoice:
    if inv.status != "pending":
        raise ValueError("Only pending invoices can be sent")
    inv.dte_number = inv.dte_number or f"DTE-{inv.id:06d}"
    inv.status = "accepted"
    db.commit()
    log_action(db, project_id=inv.project_id, entity="invoice", entity_id=inv.id, action="invoice_send_sii", data={"dte_number": inv.dte_number}, user_id=user_id)
    return inv


def register_payment(db: Session, user_id: int, inv: Invoice, amount: float, method: str, reference: str | None) -> Invoice:
    pay = InvoicePayment(invoice_id=inv.id, amount=amount, method=method, reference=reference)
    db.add(pay)
    paid_total = db.query(func.coalesce(func.sum(InvoicePayment.amount), 0)).filter(InvoicePayment.invoice_id == inv.id).scalar() or 0
    paid_total = Decimal(str(paid_total))
    amt = Decimal(str(amount))
    inv_amount = Decimal(str(inv.amount))
    if paid_total + amt >= inv_amount:
        inv.status = "paid"
    db.commit()
    db.refresh(inv)
    log_action(db, project_id=inv.project_id, entity="invoice", entity_id=inv.id, action="invoice_payment", data={"payment": str(amount)}, user_id=user_id)
    return inv


def import_bank_transactions(db: Session, user_id: int, project_id: int, items: List[Dict], source: str) -> int:
    created = 0
    for item in items:
        dt = item.get('date')
        if isinstance(dt, str):
            try:
                parts = dt.split('-')
                if len(parts) == 3:
                    dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                dt = None
        bt = BankTransaction(
            project_id=project_id,
            date=dt,
            description=item.get('description'),
            amount=item.get('amount'),
            balance=item.get('balance'),
            source=source,
            raw=item
        )
        db.add(bt)
        created += 1
    db.commit()
    log_action(db, project_id=project_id, entity="project", entity_id=project_id, action="bank_import", data={"count": created}, user_id=user_id)
    return created


def reconcile_transaction(db: Session, user_id: int, bt: BankTransaction, inv: Invoice):
    bt.matched_invoice_id = inv.id
    if inv.status in ("accepted", "pending") and abs(float(bt.amount) - float(inv.amount)) < 0.01:
        inv.status = "paid"
    db.commit()
    log_action(db, project_id=inv.project_id, entity="invoice", entity_id=inv.id, action="bank_reconcile", data={"bank_txn": bt.id}, user_id=user_id)
    return inv.status


def financial_metrics(db: Session, project_id: int) -> dict:
    total = db.query(func.coalesce(func.sum(Invoice.amount), 0)).filter(Invoice.project_id == project_id).scalar() or 0
    paid = db.query(func.coalesce(func.sum(Invoice.amount), 0)).filter(Invoice.project_id == project_id, Invoice.status == 'paid').scalar() or 0
    pending = total - paid
    ratio = (paid / total) if total else 0
    return {"invoiced_total": float(total), "paid_total": float(paid), "pending_total": float(pending), "paid_ratio": ratio}
