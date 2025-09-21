from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.budget import Item, Chapter, MeasurementBatch, MeasurementLine

router = APIRouter()


@router.get("/projects/{project_id}")
def evm_overview(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Cargar items presupuesto
    items = db.query(Item).join(Chapter, Item.chapter_id==Chapter.id).filter(Chapter.project_id==project_id, Item.deleted_at.is_(None), Chapter.deleted_at.is_(None)).all()
    if not items:
        # Retornar métricas vacías en lugar de 404 para facilitar consumo temprano
        return {"project_id": project_id, "planned_value": 0, "earned_value": 0, "actual_cost": 0, "spi": 0, "cpi": 0, "curve_s": []}
    def _f(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    total_budget = 0.0
    for it in items:
        total_budget += _f(it.quantity) * _f(it.price)
    # EV y AC (por ahora AC = EV al no tener costos reales separados)
    # Ejecutado por item
    sub_exec = db.query(
        MeasurementLine.item_id,
        func.coalesce(func.sum(MeasurementLine.qty), 0).label("exec_qty")
    ).join(MeasurementBatch, MeasurementLine.batch_id==MeasurementBatch.id).filter(
        MeasurementBatch.project_id==project_id,
        MeasurementBatch.status=='closed'
    ).group_by(MeasurementLine.item_id).subquery()
    earned_value = 0.0
    for it in items:
        exec_row = db.query(sub_exec.c.exec_qty).filter(sub_exec.c.item_id==it.id).first()
        exec_qty = _f(exec_row[0]) if exec_row and exec_row[0] is not None else 0.0
        earned_value += exec_qty * _f(it.price)
    planned_value = total_budget  # simplificación: PV total asumido igual al presupuesto completo (sin calendario)
    actual_cost = earned_value  # sin costo real separado aún
    spi = (earned_value / planned_value) if planned_value > 0 else 0
    cpi = (earned_value / actual_cost) if actual_cost > 0 else 0

    # Curva S: acumulado EV por batch cerrado en orden cronológico
    batches = db.query(MeasurementBatch).filter(
        MeasurementBatch.project_id==project_id,
        MeasurementBatch.status=='closed'
    ).order_by(MeasurementBatch.created_at).all()
    curve = []
    cumulative_ev = 0.0
    for b in batches:
        # EV batch = suma qty * precio item para líneas del batch
        lines = db.query(MeasurementLine, Item).join(Item, MeasurementLine.item_id==Item.id).filter(MeasurementLine.batch_id==b.id).all()
        batch_ev = 0.0
        for ml, it in lines:
            batch_ev += _f(ml.qty) * _f(it.price)
        cumulative_ev += batch_ev
        curve.append({
            "batch_id": b.id,
            "name": b.name,
            "status": b.status,
            "batch_ev": batch_ev,
            "cumulative_ev": cumulative_ev,
            "created_at": b.created_at
        })

    return {
        "project_id": project_id,
        "planned_value": planned_value,
        "earned_value": earned_value,
        "actual_cost": actual_cost,
        "spi": spi,
        "cpi": cpi,
        "curve_s": curve
    }
