from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.versioning import BudgetVersion, BudgetVersionItem
from app.db.models.budget import Item, Chapter
from app.db.models.project import Project

router = APIRouter()

def snapshot_logic(db: Session, project_id: int, name: str, note: str | None):
    v = BudgetVersion(project_id=project_id, name=name, note=note)
    db.add(v); db.flush()
    items = db.query(Item).join(Chapter, Chapter.id==Item.chapter_id).filter(Chapter.project_id==project_id).all()
    for it in items:
        db.add(BudgetVersionItem(version_id=v.id, item_code=it.code, item_name=it.name, unit=it.unit, qty=it.quantity, unit_price=it.price))
    db.commit(); return v.id

def diff_logic(db: Session, v_from: int, v_to: int):
    A = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==v_from).all()
    B = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==v_to).all()
    mapA = {a.item_code: a for a in A}
    mapB = {b.item_code: b for b in B}
    added = list(mapB.keys() - mapA.keys())
    removed = list(mapA.keys() - mapB.keys())
    changed = []
    for code in mapA.keys() & mapB.keys():
        a, b = mapA[code], mapB[code]
        if a.qty != b.qty or a.unit_price != b.unit_price:
            changed.append({
                "code": code,
                "qty_from": float(a.qty), "qty_to": float(b.qty),
                "pu_from": float(a.unit_price), "pu_to": float(b.unit_price),
                "delta_total": float(b.qty*b.unit_price - a.qty*a.unit_price)
            })
    return {"added": added, "removed": removed, "changed": changed}

@router.post("/{project_id}/snapshot")
async def snapshot(project_id: int, name: str, note: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    vid = snapshot_logic(db, project_id, name, note)
    return {"version_id": vid}

@router.get("/diff")
async def diff(v_from: int, v_to: int, db: Session = Depends(get_db)):
    return diff_logic(db, v_from, v_to)

@router.post("/{project_id}/baseline")
def set_baseline(project_id: int, version_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    ver = db.get(BudgetVersion, version_id)
    if not ver or ver.project_id != project_id:
        raise HTTPException(400, "Version inválida para este proyecto")
    project.baseline_version_id = version_id
    db.commit()
    return {"project_id": project_id, "baseline_version_id": version_id}

