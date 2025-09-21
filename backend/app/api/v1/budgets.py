from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from app.services.kpis import compute_item_price
from app.services.audit import log_action
from app.services.rbac import require_role, check_role
from app.db.models.audit import UserProjectRole
from sqlalchemy import desc, func

router = APIRouter()

class ProjectIn(BaseModel):
    name: str
    currency: str = "CLP"

@router.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@router.post("/projects")
async def create_project(p: ProjectIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = Project(name=p.name, currency=p.currency)
    db.add(obj); db.flush()
    upr = UserProjectRole(user_id=user.id, project_id=obj.id, role="admin")
    db.add(upr)
    db.commit(); db.refresh(obj)
    log_action(db, obj.id, "project", obj.id, "create", {"name": obj.name, "currency": obj.currency}, user.id)
    return {"id": obj.id, "name": obj.name, "currency": obj.currency}

class ChapterIn(BaseModel):
    project_id: int
    code: str
    name: str

@router.post("/chapters")
async def create_chapter(c: ChapterIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Verificación de rol (admin o editor) dinámica porque no hay project_id en path
    check_role(db, user.id, c.project_id, ["admin", "editor"])
    # Pydantic v2: reemplazar dict() por model_dump()
    obj = Chapter(**c.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    log_action(db, c.project_id, "chapter", obj.id, "create", {"code": obj.code, "name": obj.name}, user.id)
    return {"id": obj.id, "code": obj.code, "name": obj.name}

@router.get("/projects/{project_id}/chapters")
async def list_chapters(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    rows = db.query(Chapter).filter(Chapter.project_id==project_id, Chapter.deleted_at.is_(None)).order_by(Chapter.id).all()
    return [{"id": r.id, "code": r.code, "name": r.name} for r in rows]

class ChapterUpdate(BaseModel):
    code: str | None = None
    name: str | None = None

@router.patch("/chapters/{chapter_id}")
async def update_chapter(chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ch = db.get(Chapter, chapter_id)
    if not ch or ch.deleted_at is not None:
        raise HTTPException(404, "Chapter not found")
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    changed = {}
    if payload.code is not None:
        ch.code = payload.code; changed["code"] = payload.code
    if payload.name is not None:
        ch.name = payload.name; changed["name"] = payload.name
    if not changed:
        return {"id": ch.id, "code": ch.code, "name": ch.name}
    db.commit(); db.refresh(ch)
    log_action(db, ch.project_id, "chapter", ch.id, "update_chapter", changed, user.id)
    return {"id": ch.id, "code": ch.code, "name": ch.name}

@router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ch = db.get(Chapter, chapter_id)
    if not ch or ch.deleted_at is not None:
        raise HTTPException(404, "Chapter not found")
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    ch.deleted_at = func.now()
    db.commit()
    log_action(db, ch.project_id, "chapter", ch.id, "delete_chapter", {}, user.id)
    return {"status": "deleted", "id": ch.id}

class ItemIn(BaseModel):
    chapter_id: int
    code: str
    name: str
    unit: str = "m2"
    quantity: float = 0

@router.post("/items")
async def create_item(i: ItemIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ch = db.get(Chapter, i.chapter_id)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    # Pydantic v2: reemplazar dict() por model_dump()
    obj = Item(**i.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    log_action(db, ch.project_id, "item", obj.id, "create", {"code": obj.code, "name": obj.name}, user.id)
    return {"id": obj.id, "code": obj.code, "name": obj.name}

@router.get("/chapters/{chapter_id}/items")
async def list_items(chapter_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ch = db.get(Chapter, chapter_id)
    if not ch or ch.deleted_at is not None:
        raise HTTPException(404, "Chapter not found")
    check_role(db, user.id, ch.project_id, ["admin", "editor", "viewer"])
    rows = db.query(Item).filter(Item.chapter_id==chapter_id, Item.deleted_at.is_(None)).order_by(Item.id).all()
    return [{"id": r.id, "code": r.code, "name": r.name} for r in rows]

class ItemUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    unit: str | None = None
    quantity: float | None = None

@router.patch("/items/{item_id}")
async def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    it = db.get(Item, item_id)
    if not it or it.deleted_at is not None:
        raise HTTPException(404, "Item not found")
    ch = db.get(Chapter, it.chapter_id)
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    changed = {}
    if payload.code is not None: it.code = payload.code; changed["code"] = payload.code
    if payload.name is not None: it.name = payload.name; changed["name"] = payload.name
    if payload.unit is not None: it.unit = payload.unit; changed["unit"] = payload.unit
    if payload.quantity is not None: it.quantity = payload.quantity; changed["quantity"] = str(payload.quantity)
    if not changed:
        return {"id": it.id, "code": it.code, "name": it.name}
    db.commit(); db.refresh(it)
    log_action(db, ch.project_id, "item", it.id, "update_item", changed, user.id)
    return {"id": it.id, "code": it.code, "name": it.name}

@router.delete("/items/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    it = db.get(Item, item_id)
    if not it or it.deleted_at is not None:
        raise HTTPException(404, "Item not found")
    ch = db.get(Chapter, it.chapter_id)
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    it.deleted_at = func.now()
    db.commit()
    log_action(db, ch.project_id, "item", it.id, "delete_item", {}, user.id)
    return {"status": "deleted", "id": it.id}

class APULineIn(BaseModel):
    resource_code: str
    resource_name: str
    resource_type: str
    unit: str = "u"
    unit_cost: float
    coeff: float

@router.post("/items/{item_id}/apu")
async def set_apu(item_id: int, lines: list[APULineIn], db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    ch = db.get(Chapter, item.chapter_id)
    check_role(db, user.id, ch.project_id, ["admin", "editor"])
    apu_payload = []
    # Limpiar APU existente (asumido sobrescribe)
    db.query(APU).filter(APU.item_id==item.id).delete()
    for l in lines:
        r = db.query(Resource).filter(Resource.code==l.resource_code).first()
        if not r:
            r = Resource(code=l.resource_code, name=l.resource_name, type=l.resource_type, unit=l.unit, unit_cost=l.unit_cost)
            db.add(r); db.flush()
        apu = APU(item_id=item.id, resource_id=r.id, coeff=l.coeff)
        db.add(apu)
        apu_payload.append({"coeff": l.coeff, "unit_cost": l.unit_cost})
    item.price = compute_item_price(apu_payload)
    db.commit(); db.refresh(item)
    log_action(db, ch.project_id, "item", item.id, "set_apu", {"lines": len(lines), "price": str(item.price)}, user.id)
    return {"item_id": item.id, "price": str(item.price), "lines": len(lines)}

class RoleAssignIn(BaseModel):
    user_id: int
    role: str

@router.post("/projects/{project_id}/roles")
async def assign_role(project_id: int, payload: RoleAssignIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Solo admin puede asignar
    check_role(db, user.id, project_id, ["admin"])
    if payload.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(400, "Rol inválido")
    existing = db.query(UserProjectRole).filter_by(user_id=payload.user_id, project_id=project_id).first()
    if existing:
        existing.role = payload.role
    else:
        db.add(UserProjectRole(user_id=payload.user_id, project_id=project_id, role=payload.role))
    db.commit()
    log_action(db, project_id, "user_project_role", payload.user_id, "assign_role", {"role": payload.role}, user.id)
    return {"user_id": payload.user_id, "project_id": project_id, "role": payload.role}

@router.get("/projects/{project_id}/roles")
async def list_roles(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    rows = db.query(UserProjectRole).filter_by(project_id=project_id).all()
    return [{"user_id": r.user_id, "role": r.role} for r in rows]

@router.get("/projects/{project_id}/audit")
async def list_audit(project_id: int, limit: int = 50, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Cualquier rol con acceso al proyecto puede ver la auditoría
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    from app.db.models.audit import AuditLog  # import local para evitar ciclos
    q = db.query(AuditLog).filter(AuditLog.project_id==project_id).order_by(desc(AuditLog.id)).limit(min(limit, 200)).all()
    return [
        {"id": a.id, "entity": a.entity, "entity_id": a.entity_id, "action": a.action, "data": a.data, "user_id": a.user_id, "created_at": a.created_at}
        for a in q
    ]


# -------------------- Tree & Summary --------------------

@router.get("/projects/{project_id}/tree")
async def project_tree(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Cualquier rol con acceso puede ver
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    chapters = db.query(Chapter).filter(Chapter.project_id==project_id, Chapter.deleted_at.is_(None)).order_by(Chapter.id).all()
    # Pre-cargar items por capítulo (N+1 simple dado tamaño reducido; optimizable si fuese grande)
    chapter_ids = [c.id for c in chapters]
    items = []
    if chapter_ids:
        items = db.query(Item).filter(Item.chapter_id.in_(chapter_ids), Item.deleted_at.is_(None)).order_by(Item.id).all()
    items_by_ch = {}
    for it in items:
        items_by_ch.setdefault(it.chapter_id, []).append({
            "id": it.id,
            "code": it.code,
            "name": it.name,
            "unit": it.unit,
            "quantity": float(it.quantity or 0),
            "price": float(it.price or 0)
        })
    tree = []
    for ch in chapters:
        tree.append({
            "id": ch.id,
            "code": ch.code,
            "name": ch.name,
            "items": items_by_ch.get(ch.id, [])
        })
    return {"project_id": project_id, "chapters": tree}


@router.get("/projects/{project_id}/summary")
async def project_summary(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    total_chapters = db.query(func.count(Chapter.id)).filter(Chapter.project_id==project_id, Chapter.deleted_at.is_(None)).scalar() or 0
    # Items
    q_items = db.query(
        func.count(Item.id),
        func.coalesce(func.sum(Item.quantity), 0),
        func.coalesce(func.sum(Item.quantity * Item.price), 0)
    ).join(Chapter, Item.chapter_id==Chapter.id).filter(Chapter.project_id==project_id, Chapter.deleted_at.is_(None), Item.deleted_at.is_(None)).one()
    total_items, total_quantity, total_cost = q_items
    return {
        "project_id": project_id,
        "total_chapters": int(total_chapters),
        "total_items": int(total_items or 0),
        "total_quantity": float(total_quantity or 0),
        "total_cost": float(total_cost or 0)
    }
