from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.versioning import BudgetVersion, BudgetVersionItem
from app.db.models.budget import Item, Chapter
from app.db.models.project import Project
from app.services.audit import log_action
from app.services.rbac import require_role, check_role

router = APIRouter()

def snapshot_logic(db: Session, project_id: int, name: str, note: str | None, user_id: int | None = None):
    v = BudgetVersion(project_id=project_id, name=name, note=note, created_by=user_id)
    db.add(v); db.flush()
    rows = db.query(Item, Chapter).join(Chapter, Chapter.id==Item.chapter_id).filter(Chapter.project_id==project_id).all()
    for it, ch in rows:
        db.add(BudgetVersionItem(version_id=v.id, chapter_code=ch.code, chapter_name=ch.name, item_code=it.code, item_name=it.name, unit=it.unit, qty=it.quantity, unit_price=it.price))
    db.commit(); return v.id

def diff_logic(db: Session, v_from: int, v_to: int):
    A = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==v_from).all()
    B = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==v_to).all()
    mapA = {a.item_code: a for a in A}
    mapB = {b.item_code: b for b in B}
    added = list(mapB.keys() - mapA.keys())
    removed = list(mapA.keys() - mapB.keys())
    changed = []
    def _f(val):
        try:
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0
    for code in mapA.keys() & mapB.keys():
        a, b = mapA[code], mapB[code]
        if _f(a.qty) != _f(b.qty) or _f(a.unit_price) != _f(b.unit_price):
            changed.append({
                "code": code,
                "qty_from": _f(a.qty), "qty_to": _f(b.qty),
                "pu_from": _f(a.unit_price), "pu_to": _f(b.unit_price),
                "delta_total": _f(b.qty)*_f(b.unit_price) - _f(a.qty)*_f(a.unit_price)
            })
    return {"added": added, "removed": removed, "changed": changed}

@router.post("/{project_id}/snapshot")
async def snapshot(project_id: int, name: str, note: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # rol editor o admin
    check_role(db, user.id, project_id, ["admin", "editor"])
    vid = snapshot_logic(db, project_id, name, note, user_id=user.id)
    log_action(db, project_id, "version", int(vid), "snapshot", {"name": name, "note": note}, user.id)
    return {"version_id": vid}

@router.get("/diff")
async def diff(v_from: int, v_to: int, db: Session = Depends(get_db)):
    return diff_logic(db, v_from, v_to)

@router.get("/{project_id}/versions")
def list_versions(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(BudgetVersion).filter(BudgetVersion.project_id==project_id).order_by(BudgetVersion.created_at.desc()).all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "note": v.note,
            "created_at": v.created_at,
            "created_by": v.created_by,
            "is_baseline": v.is_baseline,
            "is_locked": v.is_locked
        } for v in q
    ]

@router.get("/version/{version_id}")
def version_detail(version_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    v = db.get(BudgetVersion, version_id)
    if v is None:
        raise HTTPException(404, "Version no encontrada")
    items = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==version_id).all()
    def _f(x):
        try:
            return float(x) if x is not None else 0.0
        except Exception:
            return 0.0
    return {
        "id": v.id,
        "project_id": v.project_id,
        "name": v.name,
        "note": v.note,
        "created_at": v.created_at,
        "lines": [
                {"chapter_code": li.chapter_code, "chapter_name": li.chapter_name, "item_code": li.item_code, "item_name": li.item_name, "unit": li.unit, "qty": _f(li.qty), "unit_price": _f(li.unit_price)}
            for li in items
        ]
    }

@router.get("/diff/live")
def diff_live(project_id: int, version_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # diff entre una versión y estado actual
    ver_items = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==version_id).all()
    mapV = {vi.item_code: vi for vi in ver_items}
    current = db.query(Item, Chapter).join(Chapter, Chapter.id==Item.chapter_id).filter(Chapter.project_id==project_id).all()
    mapC = {it.code: (it, ch) for it, ch in current}
    added = list(mapC.keys() - mapV.keys())
    removed = list(mapV.keys() - mapC.keys())
    changed = []
    for code in mapC.keys() & mapV.keys():
        it, ch = mapC[code]; vi = mapV[code]
        def _f(x):
            try:
                return float(x) if x is not None else 0.0
            except Exception:
                return 0.0
        if _f(vi.qty) != _f(it.quantity) or _f(vi.unit_price) != _f(it.price):
            changed.append({
                "code": code,
                "qty_version": _f(vi.qty), "qty_current": _f(it.quantity),
                "pu_version": _f(vi.unit_price), "pu_current": _f(it.price),
                "delta_total": _f(it.quantity)*_f(it.price) - _f(vi.qty)*_f(vi.unit_price)
            })
    return {"added": added, "removed": removed, "changed": changed}

@router.post("/restore/{version_id}")
def restore_version(version_id: int, project_id: int, make_snapshot: bool = True, name_snapshot: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ver = db.get(BudgetVersion, version_id)
    if ver is None or (getattr(ver, 'project_id', None) != project_id):
        raise HTTPException(404, "Version inválida")
    check_role(db, user.id, project_id, ["admin", "editor"])
    if make_snapshot:
        snapshot_logic(db, project_id, name_snapshot or f"pre-restore-{version_id}", note="auto snapshot", user_id=user.id)
    # Borrar items actuales y recrear según versión
    # (Estrategia simple, sin preservar IDs; se podría mapear luego)
    items = db.query(Item).join(Chapter, Chapter.id==Item.chapter_id).filter(Chapter.project_id==project_id).all()
    for it in items:
        db.delete(it)
    db.commit()
    # Limpieza de capítulos sin ítems
    empty_chapters = db.query(Chapter).filter(Chapter.project_id==project_id).all()
    for ch in empty_chapters:
        has_items = db.query(Item.id).filter(Item.chapter_id==ch.id).first()
        if not has_items:
            db.delete(ch)
    db.commit()
    # Necesitamos capítulos destino (crear si no existen por code)
    existing_ch = {c.code: c for c in db.query(Chapter).filter(Chapter.project_id==project_id).all()}
    ver_lines = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id==version_id).all()
    for li in ver_lines:
        ch = existing_ch.get(li.chapter_code)
        if not ch:
            ch = Chapter(project_id=project_id, code=li.chapter_code, name=li.chapter_name)
            db.add(ch); db.flush()
            existing_ch[ch.code] = ch
        db.add(Item(chapter_id=ch.id, code=li.item_code, name=li.item_name, unit=li.unit, quantity=li.qty, price=li.unit_price))
    db.commit()
    log_action(db, project_id, "version", version_id, "restore", {"project_id": project_id}, user.id)
    return {"restored_version": version_id}

@router.post("/{project_id}/baseline")
def set_baseline(project_id: int, version_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin"])
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    ver = db.get(BudgetVersion, version_id)
    if ver is None or (getattr(ver, 'project_id', None) != project_id):
        raise HTTPException(400, "Version inválida para este proyecto")
    project.baseline_version_id = version_id  # type: ignore[assignment]
    db.commit()
    log_action(db, project_id, "project", project_id, "set_baseline", {"baseline_version_id": version_id}, user.id)
    return {"project_id": project_id, "baseline_version_id": version_id}

