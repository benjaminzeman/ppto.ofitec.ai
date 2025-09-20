# OFITEC · Presupuestos/Mediciones – Sprint 7-8

Este Sprint introduce **workflows de aprobación**, **dashboards unificados (finanzas + mediciones + riesgos)** y **módulo de riesgos**. Conecta directamente con los demás módulos de OFITEC (financials, site_management, ai_bridge) para entregar una visión ejecutiva.

---

## 0) Objetivos
- **Workflows de aprobación**: procesos de validación (PM → Gerente → Directorio).
- **Dashboards unificados**: combinar mediciones, finanzas y riesgos en un mismo panel.
- **Riesgos**: registro, clasificación y monitoreo de riesgos en cada proyecto.
- **Integración**: enganchar datos de project_financials y auditoría.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0004_workflows_dashboards_risks.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0004_workflows_dashboards_risks"
down_revision = "0003_audit_rbac_bc3_bim"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("entity", sa.String()),  # item|apu|po|cert
        sa.Column("entity_id", sa.Integer),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workflow_id", sa.Integer, sa.ForeignKey("workflows.id", ondelete="CASCADE")),
        sa.Column("role", sa.String()),
        sa.Column("user_id", sa.Integer),
        sa.Column("decision", sa.String()),  # approved|rejected|pending
        sa.Column("note", sa.Text()),
        sa.Column("decided_at", sa.DateTime()),
    )

    op.create_table(
        "risks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("category", sa.String()),  # financiero|plazo|técnico|contratos
        sa.Column("description", sa.Text()),
        sa.Column("probability", sa.Integer),  # 1-5
        sa.Column("impact", sa.Integer),  # 1-5
        sa.Column("status", sa.String(), server_default="open"),
        sa.Column("mitigation", sa.Text()),
        sa.Column("owner", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("risks")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
```

---

## 2) Modelos
**`backend/app/db/models/workflow.py`**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.db.base import Base

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    entity = Column(String)
    entity_id = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime)

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    role = Column(String)
    user_id = Column(Integer)
    decision = Column(String)
    note = Column(Text)
    decided_at = Column(DateTime)
```

**`backend/app/db/models/risk.py`**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.db.base import Base

class Risk(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    category = Column(String)
    description = Column(Text)
    probability = Column(Integer)
    impact = Column(Integer)
    status = Column(String)
    mitigation = Column(Text)
    owner = Column(String)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Workflows** – `backend/app/services/workflows.py`
```python
from sqlalchemy.orm import Session
from app.db.models.workflow import Workflow, WorkflowStep

def start_workflow(db: Session, project_id: int, entity: str, entity_id: int, steps: list[dict]):
    wf = Workflow(project_id=project_id, entity=entity, entity_id=entity_id, status="pending")
    db.add(wf); db.flush()
    for s in steps:
        db.add(WorkflowStep(workflow_id=wf.id, role=s["role"], user_id=s.get("user_id"), decision="pending"))
    db.commit(); return wf.id

def decide_step(db: Session, step_id: int, decision: str, note: str|None=None):
    step = db.get(WorkflowStep, step_id)
    step.decision = decision; step.note = note
    db.commit()
    wf = db.get(Workflow, step.workflow_id)
    if all(s.decision=="approved" for s in db.query(WorkflowStep).filter_by(workflow_id=wf.id)):
        wf.status = "approved"
    elif any(s.decision=="rejected" for s in db.query(WorkflowStep).filter_by(workflow_id=wf.id)):
        wf.status = "rejected"
    db.commit(); return wf.status
```

**Riesgos** – `backend/app/services/risks.py`
```python
from sqlalchemy.orm import Session
from app.db.models.risk import Risk

def register_risk(db: Session, project_id: int, category: str, description: str, probability: int, impact: int, mitigation: str, owner: str):
    r = Risk(project_id=project_id, category=category, description=description, probability=probability, impact=impact, mitigation=mitigation, owner=owner)
    db.add(r); db.commit(); return r.id

def risk_matrix(db: Session, project_id: int):
    risks = db.query(Risk).filter_by(project_id=project_id).all()
    matrix = [[0]*5 for _ in range(5)]
    for r in risks:
        matrix[r.probability-1][r.impact-1]+=1
    return matrix
```

---

## 4) API
**Workflows** – `backend/app/api/v1/workflows.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows import start_workflow, decide_step

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/start")
def start(project_id: int, entity: str, entity_id: int, steps: list[dict], db: Session = Depends(get_db)):
    return {"workflow_id": start_workflow(db, project_id, entity, entity_id, steps)}

@router.post("/decide")
def decide(step_id: int, decision: str, note: str|None=None, db: Session = Depends(get_db)):
    return {"status": decide_step(db, step_id, decision, note)}
```

**Riesgos** – `backend/app/api/v1/risks.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.risks import register_risk, risk_matrix

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/register")
def register(project_id: int, category: str, description: str, probability: int, impact: int, mitigation: str, owner: str, db: Session = Depends(get_db)):
    return {"risk_id": register_risk(db, project_id, category, description, probability, impact, mitigation, owner)}

@router.get("/{project_id}/matrix")
def matrix(project_id: int, db: Session = Depends(get_db)):
    return {"matrix": risk_matrix(db, project_id)}
```

---

## 5) Dashboards (Next.js)
**Unificados**: `/dashboard/[projectId]`
- **KPIs finanzas**: avance valorizado, OC vs real, flujo de caja.
- **KPIs mediciones**: % físico, curva S.
- **Riesgos**: matriz 5x5 visual con heatmap.
- **Workflows**: tarjetas de pendientes (mis decisiones).

**Componentes**
- `RiskMatrix.tsx`: heatmap (rojo/amarillo/verde).
- `WorkflowTasks.tsx`: lista de pasos pendientes con botones aprobar/rechazar.
- `DashboardCards.tsx`: tarjetas de KPIs financieros/mediciones.

---

## 6) Integración OFITEC
- **Workflows** se vinculan con auditoría (cada decisión genera un log).
- **Riesgos** conecta con `ai_bridge`: predicciones de impacto/plazo.
- **Dashboards** consumen datos desde `project_financials`, `measurements`, `risks`.
- **Roles RBAC** aplican a tareas de workflows y visibilidad de dashboards.

---

## 7) Checklist de cierre Sprint 7-8
- [ ] Migración 0004 aplicada.
- [ ] Workflows funcionales (inicio + decisiones).
- [ ] Riesgos registrados y matriz exportable.
- [ ] Dashboard unificado visible en frontend.
- [ ] Integración con auditoría.
- [ ] Tests Pytest para workflows y riesgos.
- [ ] Roles aplicados a endpoints y UI.

---

## 8) Próximos pasos (Sprint 9+)
- **Certificaciones**: estados de pago vinculados a versiones de presupuesto.
- **Simulación de caja**: escenarios con riesgos y desviaciones.
- **IA avanzada**: recomendación de mitigaciones en riesgos.
- **Control documental**: vincular contratos, adendas, minutas.
- **KPIs ejecutivos multi-proyecto**: tablero global con semáforos y alertas.

