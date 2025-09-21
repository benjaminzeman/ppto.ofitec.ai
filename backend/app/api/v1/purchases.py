from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.purchases import Supplier, RFQ, RFQItem, Quote, QuoteLine, PurchaseOrder, PurchaseOrderLine
from app.db.models.budget import Item, Chapter

router = APIRouter()


class SupplierIn(BaseModel):
    name: str
    tax_id: str | None = None
    contact_email: str | None = None


@router.post("/suppliers")
def create_supplier(body: SupplierIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Pydantic v2: usar model_dump() en lugar de dict()
    s = Supplier(**body.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s


@router.get("/suppliers")
def list_suppliers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Supplier).all()


class RFQCreate(BaseModel):
    project_id: int
    items: list[dict]  # {item_id, qty}


@router.post("/rfq")
def create_rfq(body: RFQCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rfq = RFQ(project_id=body.project_id)
    db.add(rfq); db.flush()
    for it in body.items:
        rfq_item = RFQItem(rfq_id=rfq.id, item_id=it["item_id"], qty=it.get("qty", 0))
        db.add(rfq_item)
    db.commit(); db.refresh(rfq)
    return {"rfq_id": rfq.id}


class QuoteIn(BaseModel):
    rfq_id: int
    supplier_id: int
    lines: list[dict]  # {rfq_item_id, unit_price}


@router.post("/quote")
def create_quote(body: QuoteIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = Quote(rfq_id=body.rfq_id, supplier_id=body.supplier_id)
    db.add(q); db.flush()
    for l in body.lines:
        db.add(QuoteLine(quote_id=q.id, rfq_item_id=l["rfq_item_id"], unit_price=l.get("unit_price", 0)))
    db.commit(); db.refresh(q)
    return {"quote_id": q.id}


@router.get("/rank/{rfq_id}")
def rank(rfq_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Ranking simple: suma total líneas por cotización
    quotes = db.query(Quote).filter(Quote.rfq_id == rfq_id).all()
    result = []
    def _f(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    for q in quotes:
        lines = db.query(QuoteLine).filter(QuoteLine.quote_id == q.id).all()
        total = sum(_f(l.unit_price) for l in lines)
        result.append({"quote_id": q.id, "supplier_id": q.supplier_id, "total": total})
    result.sort(key=lambda x: x["total"])  # menor total primero
    return result


class POCreate(BaseModel):
    project_id: int
    supplier_id: int
    lines: list[dict]  # {item_id, qty, unit_price}
    rfq_id: int | None = None


@router.post("/po")
def create_po(body: POCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    po = PurchaseOrder(project_id=body.project_id, supplier_id=body.supplier_id, rfq_id=body.rfq_id)
    db.add(po); db.flush()
    for l in body.lines:
        pol = PurchaseOrderLine(po_id=po.id, item_id=l["item_id"], qty=l.get("qty", 0), unit_price=l.get("unit_price", 0))
        db.add(pol)
    db.commit(); db.refresh(po)
    return {"po_id": po.id}


@router.get("/po/{po_id}")
def get_po(po_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO no encontrada")
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.po_id == po.id).all()
    def _to_float(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    return {
        "id": po.id,
        "project_id": po.project_id,
        "supplier_id": po.supplier_id,
        "status": po.status,
        "rfq_id": po.rfq_id,
        "lines": [
            {"id": l.id, "item_id": l.item_id, "qty": _to_float(l.qty), "unit_price": _to_float(l.unit_price)} for l in lines
        ]
    }


class POStatusUpdate(BaseModel):
    status: str  # approved, received, closed


@router.patch("/po/{po_id}/status")
def update_po_status(po_id: int, body: POStatusUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO no encontrada")
    allowed = {"approved", "received", "closed"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail="Estado inválido")
    po.status = body.status  # type: ignore[assignment]
    db.commit(); db.refresh(po)
    return {"id": po.id, "status": po.status}


@router.get("/po/project/{project_id}")
def list_pos(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.project_id == project_id).all()
    return [
        {"id": p.id, "supplier_id": p.supplier_id, "status": p.status, "rfq_id": p.rfq_id} for p in pos
    ]

