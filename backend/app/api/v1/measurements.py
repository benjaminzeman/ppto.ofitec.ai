from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from pydantic import BaseModel
from app.db.models.budget import Item, Chapter
from app.db.models.measurement import Measurement

router = APIRouter()

class MeasurementIn(BaseModel):
    item_id: int
    qty: float
    note: str | None = None
    source: str = "manual"

@router.post("")
async def create(meas: MeasurementIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = Measurement(item_id=meas.item_id, qty=meas.qty, note=meas.note, source=meas.source)
    db.add(m); db.commit(); db.refresh(m)
    return {"id": m.id}

@router.get("/{project_id}/summary")
async def summary(project_id: int, db: Session = Depends(get_db)):
    rows = []
    q = db.query(Item).join(Chapter, Chapter.id == Item.chapter_id).filter(Chapter.project_id==project_id).all()
    for it in q:
        qty_total = sum(float(m.qty) for m in db.query(Measurement).filter(Measurement.item_id==it.id))
        rows.append({
            "item_id": it.id,
            "code": it.code,
            "name": it.name,
            "unit": it.unit,
            "qty_medida": qty_total,
            "precio_unit": float(it.price or 0),
            "valor": qty_total * float(it.price or 0)
        })
    return rows
