from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.risk import Risk
from app.services.rbac import check_role
from app.services.audit import log_action

router = APIRouter()

class RiskCreate(BaseModel):
    project_id: int
    category: str
    description: str
    probability: int
    impact: int
    mitigation: str | None = None
    owner: str | None = None

class RiskUpdate(BaseModel):
    description: str | None = None
    probability: int | None = None
    impact: int | None = None
    mitigation: str | None = None
    owner: str | None = None
    status: str | None = None

@router.post("/")
def create_risk(payload: RiskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, payload.project_id, ["admin", "editor"])
    if payload.probability < 1 or payload.probability > 5 or payload.impact < 1 or payload.impact > 5:
        raise HTTPException(400, "Escala fuera de rango 1-5")
    r = Risk(project_id=payload.project_id, category=payload.category, description=payload.description,
             probability=payload.probability, impact=payload.impact, mitigation=payload.mitigation, owner=payload.owner)
    db.add(r); db.commit(); db.refresh(r)
    log_action(db, payload.project_id, "risk", r.id, "create", {"category": r.category}, user.id)
    return {"id": r.id}

@router.get("/project/{project_id}")
def list_risks(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    rows = db.query(Risk).filter(Risk.project_id==project_id).order_by(Risk.id).all()
    return [
        {"id": r.id, "category": r.category, "probability": r.probability, "impact": r.impact, "status": r.status}
        for r in rows
    ]

@router.get("/project/{project_id}/matrix")
def risk_matrix(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, project_id, ["admin", "editor", "viewer"])
    rows = db.query(Risk).filter(Risk.project_id==project_id).all()
    matrix = [[0]*5 for _ in range(5)]
    for r in rows:
        if 1 <= (r.probability or 0) <=5 and 1 <= (r.impact or 0) <=5:
            matrix[int(r.probability)-1][int(r.impact)-1] += 1
    return {"project_id": project_id, "matrix": matrix}

@router.patch("/{risk_id}")
def update_risk(risk_id: int, payload: RiskUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.get(Risk, risk_id)
    if not r:
        raise HTTPException(404, "Risk no encontrado")
    check_role(db, user.id, r.project_id, ["admin", "editor"])
    changed = {}
    for field in ["description","probability","impact","mitigation","owner","status"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(r, field, val)
            changed[field] = val
    if not changed:
        return {"id": r.id}
    db.commit(); db.refresh(r)
    log_action(db, r.project_id, "risk", r.id, "update", changed, user.id)
    return {"id": r.id, "changed": changed}