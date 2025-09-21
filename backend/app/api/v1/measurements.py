from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.budget import MeasurementBatch, MeasurementLine, Item, Chapter
from app.services.kpis import compute_item_price
from sqlalchemy import func

router = APIRouter()


class BatchCreate(BaseModel):
    project_id: int
    name: str


@router.post("/batches")
def create_batch(body: BatchCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    b = MeasurementBatch(project_id=body.project_id, name=body.name)
    db.add(b); db.commit(); db.refresh(b)
    return {"batch_id": b.id}


class BatchLineIn(BaseModel):
    batch_id: int
    lines: list[dict]  # {item_id, qty}


@router.post("/batches/lines")
def add_lines(body: BatchLineIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    batch = db.query(MeasurementBatch).filter(MeasurementBatch.id == body.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    if str(batch.status) != "open":  # asegurar comparación a str
        raise HTTPException(status_code=400, detail="Batch cerrado")
    for l in body.lines:
        ml = MeasurementLine(batch_id=batch.id, item_id=l["item_id"], qty=l.get("qty", 0))
        db.add(ml)
    db.commit()
    return {"batch_id": batch.id, "added": len(body.lines)}


@router.post("/batches/{batch_id}/close")
def close_batch(batch_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    batch = db.query(MeasurementBatch).filter(MeasurementBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    batch.status = "closed"  # type: ignore[assignment]
    db.commit(); db.refresh(batch)
    return {"id": batch.id, "status": batch.status}


@router.get("/project/{project_id}/progress")
def project_progress(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Suma acumulada de qty por item (todas las líneas de batches cerrados)
    sub = db.query(
        MeasurementLine.item_id,
        func.coalesce(func.sum(MeasurementLine.qty), 0).label("executed_qty")
    ).join(MeasurementBatch, MeasurementLine.batch_id == MeasurementBatch.id).filter(MeasurementBatch.project_id == project_id).group_by(MeasurementLine.item_id).subquery()

    # Obtener items del proyecto
    items = db.query(Item).join(Chapter, Item.chapter_id == Chapter.id).filter(Chapter.project_id == project_id, Item.deleted_at.is_(None), Chapter.deleted_at.is_(None)).all()
    result = []
    total_budget = 0.0
    total_executed = 0.0
    def _f(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    for it in items:
        budget_qty = _f(it.quantity)
        price = _f(it.price)
        total_budget += budget_qty * price
        executed_row = db.query(sub.c.executed_qty).filter(sub.c.item_id == it.id).first()
        executed_qty = float(executed_row[0]) if executed_row and executed_row[0] is not None else 0.0
        executed_cost = executed_qty * price
        total_executed += executed_cost
        pct = (executed_qty / budget_qty * 100) if budget_qty > 0 else 0
        result.append({
            "item_id": it.id,
            "code": it.code,
            "budget_qty": budget_qty,
            "executed_qty": executed_qty,
            "unit_price": price,
            "executed_cost": executed_cost,
            "progress_pct": pct
        })
    overall_pct = (total_executed / total_budget * 100) if total_budget > 0 else 0
    return {"project_id": project_id, "items": result, "total_budget_cost": total_budget, "total_executed_cost": total_executed, "executed_pct": overall_pct}
