from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from pydantic import BaseModel
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.versioning import Workflow, WorkflowStep, WorkflowInstance, WorkflowInstanceStep
from app.services.rbac import check_role
from app.services.audit import log_action

router = APIRouter()

class WorkflowCreate(BaseModel):
    project_id: int
    name: str
    entity_type: str
    steps: list[str]  # lista de roles en orden

@router.post("/")
def create_workflow(body: WorkflowCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_role(db, user.id, body.project_id, ["admin"])  # solo admin define workflow
    wf = Workflow(project_id=body.project_id, name=body.name, entity_type=body.entity_type)
    db.add(wf); db.flush()
    pos = 1
    for role in body.steps:
        db.add(WorkflowStep(workflow_id=wf.id, position=pos, role_required=role, name=f"Step {pos}"))
        pos += 1
    db.commit(); log_action(db, body.project_id, "workflow", wf.id, "create", {"steps": len(body.steps)}, user.id)
    return {"workflow_id": wf.id}

@router.get("/{project_id}")
def list_workflows(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    wfs = db.query(Workflow).filter(Workflow.project_id==project_id, Workflow.active==True).all()
    return [{"id": w.id, "name": w.name, "entity_type": w.entity_type} for w in wfs]

class StartInstance(BaseModel):
    workflow_id: int
    entity_type: str
    entity_id: int

@router.post("/start")
def start_instance(body: StartInstance, db: Session = Depends(get_db), user=Depends(get_current_user)):
    wf = db.get(Workflow, body.workflow_id)
    if not wf or wf.entity_type != body.entity_type:
        raise HTTPException(400, "Workflow inválido")
    check_role(db, user.id, wf.project_id, ["admin", "editor"])  # iniciar
    inst = WorkflowInstance(workflow_id=wf.id, project_id=wf.project_id, entity_type=body.entity_type, entity_id=body.entity_id, created_by=user.id)
    db.add(inst); db.flush()
    steps = db.query(WorkflowStep).filter(WorkflowStep.workflow_id==wf.id).order_by(WorkflowStep.position).all()
    for s in steps:
        db.add(WorkflowInstanceStep(instance_id=inst.id, step_id=s.id, position=s.position))
    db.commit(); log_action(db, wf.project_id, "workflow_instance", inst.id, "start", {"entity_id": body.entity_id}, user.id)
    return {"instance_id": inst.id}

@router.get("/instance/{instance_id}")
def instance_detail(instance_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inst = db.get(WorkflowInstance, instance_id)
    if not inst:
        raise HTTPException(404, "Instance no encontrada")
    steps = db.query(WorkflowInstanceStep).filter(WorkflowInstanceStep.instance_id==inst.id).order_by(WorkflowInstanceStep.position).all()
    return {
        "id": inst.id,
        "status": inst.status,
        "current_step": inst.current_step,
        "entity_type": inst.entity_type,
        "entity_id": inst.entity_id,
        "steps": [
            {"position": st.position, "decision": st.decision, "decided_by": st.decided_by, "comment": st.comment}
            for st in steps
        ]
    }

class DecideBody(BaseModel):
    decision: str  # approve/reject
    comment: str | None = None

@router.post("/instance/{instance_id}/decide")
def decide(instance_id: int, body: DecideBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inst = db.get(WorkflowInstance, instance_id)
    if not inst or inst.status != "running":
        raise HTTPException(400, "Instancia no válida para decisión")
    # obtener step actual
    step = db.query(WorkflowInstanceStep).filter(WorkflowInstanceStep.instance_id==inst.id, WorkflowInstanceStep.position==inst.current_step).first()
    if not step:
        raise HTTPException(400, "Step actual no encontrado")
    # verificar rol usuario
    wf_step = db.get(WorkflowStep, step.step_id)
    check_role(db, user.id, inst.project_id, [wf_step.role_required])
    if body.decision not in ("approve", "reject"):
        raise HTTPException(400, "Decisión inválida")
    step.decision = body.decision
    step.decided_by = user.id
    step.decided_at = datetime.utcnow()
    step.comment = body.comment
    if body.decision == "reject":
        inst.status = "rejected"  # type: ignore[assignment]
    else:
        # verificar si hay más steps
        next_step = db.query(WorkflowInstanceStep).filter(WorkflowInstanceStep.instance_id==inst.id, WorkflowInstanceStep.position==inst.current_step+1).first()
        if next_step:
            inst.current_step += 1  # type: ignore[assignment]
        else:
            inst.status = "approved"  # type: ignore[assignment]
    db.commit(); log_action(db, inst.project_id, "workflow_instance", inst.id, "decide", {"decision": step.decision, "step": step.position}, user.id)
    return {"status": inst.status, "current_step": inst.current_step}
