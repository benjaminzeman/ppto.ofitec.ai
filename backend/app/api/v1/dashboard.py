from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.rbac import check_role
from app.db.models.budget import Chapter, Item, MeasurementBatch, MeasurementLine
from app.db.models.risk import Risk
from app.db.models.versioning import WorkflowInstance, WorkflowInstanceStep, WorkflowStep
from app.db.models.audit import UserProjectRole
from app.services.invoices import financial_metrics

router = APIRouter()

def _float(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0

@router.get('/projects/{project_id}')
def project_dashboard(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # RBAC lectura
    check_role(db, int(user.id), int(project_id), ["admin", "editor", "viewer"])

    # --- Presupuesto (PV) ---
    pv = db.query(func.coalesce(func.sum(Item.quantity * Item.price), 0)) \
        .join(Chapter, Item.chapter_id == Chapter.id) \
        .filter(
            Chapter.project_id == project_id,
            Chapter.deleted_at.is_(None),
            Item.deleted_at.is_(None)
        ).scalar() or 0

    # --- Valor ganado (EV) usando solo batches cerrados ---
    ev = db.query(func.coalesce(func.sum(MeasurementLine.qty * Item.price), 0)) \
        .join(MeasurementBatch, MeasurementLine.batch_id == MeasurementBatch.id) \
        .join(Item, Item.id == MeasurementLine.item_id) \
        .join(Chapter, Chapter.id == Item.chapter_id) \
        .filter(
            MeasurementBatch.project_id == project_id,
            MeasurementBatch.status == 'closed',
            Chapter.project_id == project_id,
            Chapter.deleted_at.is_(None),
            Item.deleted_at.is_(None)
        ).scalar() or 0

    # Riesgos: conteos y matriz ligera (totales open vs closed)
    risk_counts = db.query(
        func.coalesce(func.sum(case((Risk.status=='open',1), else_=0)),0).label('open'),
        func.coalesce(func.sum(case((Risk.status=='mitigating',1), else_=0)),0).label('mitigating'),
        func.coalesce(func.sum(case((Risk.status=='closed',1), else_=0)),0).label('closed')
    ).filter(Risk.project_id==project_id).one()

    # Roles del usuario en el proyecto (normalmente 1)
    user_role = db.query(UserProjectRole).filter_by(user_id=int(user.id), project_id=int(project_id)).first()
    role_list = [user_role.role] if user_role else []

    # Pasos pendientes totales (sin decisión, instancias en ejecución y en el paso actual)
    pending_total_q = db.query(func.count(WorkflowInstanceStep.id)) \
        .join(WorkflowInstance, WorkflowInstanceStep.instance_id == WorkflowInstance.id) \
        .join(WorkflowStep, WorkflowInstanceStep.step_id == WorkflowStep.id) \
        .filter(
            WorkflowInstance.project_id == project_id,
            WorkflowInstance.status == 'running',
            WorkflowInstanceStep.decision.is_(None),
            WorkflowInstanceStep.position == WorkflowInstance.current_step
        )
    pending_total = pending_total_q.scalar() or 0

    # Pasos pendientes para el usuario (filtrando por rol requerido)
    if role_list:
        pending_user_q = pending_total_q.filter(WorkflowStep.role_required.in_(role_list))
        pending_user = pending_user_q.scalar() or 0
    else:
        pending_user = 0

    fin = financial_metrics(db, project_id)

    return {
        'project_id': project_id,
        'budget': {
            'pv': _float(pv),
            'ev': _float(ev),
            'progress_percent': (_float(ev)/_float(pv)*100) if pv else 0.0
        },
        'finance': fin,
        'risks': {
            'open': int(risk_counts.open),
            'mitigating': int(risk_counts.mitigating),
            'closed': int(risk_counts.closed)
        },
        'workflows': {
            'pending_steps': int(pending_user),  # compat: campo existente ahora específico del usuario
            'pending_steps_total': int(pending_total)
        }
    }