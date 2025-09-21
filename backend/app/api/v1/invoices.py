from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.rbac import assert_project_access
from app.db.models.versioning import Invoice, BankTransaction
from app.services.invoices import (
    create_invoice as svc_create_invoice,
    list_invoices as svc_list_invoices,
    send_sii as svc_send_sii,
    register_payment as svc_register_payment,
    import_bank_transactions as svc_import_bank,
    reconcile_transaction as svc_reconcile
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


class InvoiceCreate(BaseModel):
    project_id: int
    amount: float
    currency: str = "CLP"
    dte_number: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    project_id: int
    amount: float
    currency: str
    status: str
    dte_number: Optional[str]
    class Config:
        orm_mode = True
        from_attributes = True


class SendSIIResponse(BaseModel):
    id: int
    status: str
    dte_number: str
    class Config:
        orm_mode = True
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: float
    method: str
    reference: Optional[str] = None


class BankTxnImport(BaseModel):
    project_id: int
    items: List[dict]
    source: str = "manual"


class ReconcileRequest(BaseModel):
    bank_txn_id: int
    invoice_id: int


@router.post("/", response_model=InvoiceOut)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assert_project_access(db, user, int(data.project_id))
    return svc_create_invoice(db, user.id, data.project_id, data.amount, data.currency, data.dte_number)


@router.get("/", response_model=List[InvoiceOut])
def list_invoices(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assert_project_access(db, user, int(project_id))
    return svc_list_invoices(db, project_id)


@router.post("/{invoice_id}/send_sii", response_model=SendSIIResponse)
def send_sii(invoice_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    assert_project_access(db, user, int(inv.project_id))
    try:
        inv = svc_send_sii(db, user.id, inv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SendSIIResponse(id=inv.id, status=inv.status, dte_number=inv.dte_number)


@router.post("/{invoice_id}/payments", response_model=InvoiceOut)
def register_payment(invoice_id: int, data: PaymentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    assert_project_access(db, user, inv.project_id)
    return svc_register_payment(db, user.id, inv, data.amount, data.method, data.reference)


@router.post("/bank/import", response_model=dict)
def import_bank(data: BankTxnImport, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assert_project_access(db, user, int(data.project_id))
    created = svc_import_bank(db, user.id, data.project_id, data.items, data.source)
    return {"created": created}


@router.post("/bank/reconcile", response_model=dict)
def reconcile(req: ReconcileRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bt = db.query(BankTransaction).filter(BankTransaction.id == req.bank_txn_id).first()
    inv = db.query(Invoice).filter(Invoice.id == req.invoice_id).first()
    if not bt or not inv:
        raise HTTPException(status_code=404, detail="Not found")
    assert_project_access(db, user, int(bt.project_id))
    if int(bt.project_id) != int(inv.project_id):
        raise HTTPException(status_code=400, detail="Project mismatch")
    status = svc_reconcile(db, user.id, bt, inv)
    return {"matched": True, "invoice_status": status}
