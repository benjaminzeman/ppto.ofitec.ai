# OFITEC · Presupuestos/Mediciones – Sprint 37-38

Este Sprint consolida la **toma de decisiones estratégicas**: multi-escenarios financieros, IA explicativa, workflows configurables y un panel ejecutivo único.

---

## 0) Objetivos
- **Forecast multi-escenarios**: generar proyecciones optimista/base/pesimista.
- **IA explicativa**: detallar por qué se sugiere una acción o decisión.
- **Workflows por rol**: configurar aprobaciones según jerarquía.
- **Panel ejecutivo único**: integrar forecast, IA y workflows en una sola vista.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0019_multi_scenarios_ai_roles_panel.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0019_multi_scenarios_ai_roles_panel"
down_revision = "0018_forecast_global_ai_bi_workflows"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "workflow_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role", sa.String()),
        sa.Column("permissions", sa.JSON()),
    )

def downgrade():
    op.drop_table("workflow_roles")
```

---

## 2) Modelos
**`backend/app/db/models/workflow_role.py`**
```python
from sqlalchemy import Column, Integer, String, JSON
from app.db.base import Base

class WorkflowRole(Base):
    __tablename__ = "workflow_roles"
    id = Column(Integer, primary_key=True)
    role = Column(String)
    permissions = Column(JSON)
```

---

## 3) Servicios
**Forecast multi-escenarios** – `backend/app/services/forecast_scenarios.py`
```python
import random

def forecast_scenarios(company_id: int, years: int=3):
    scenarios = ["optimista","base","pesimista"]
    out={}
    for s in scenarios:
        out[s]=[]
        for y in range(years):
            factor = 1.2 if s=="optimista" else 0.8 if s=="pesimista" else 1
            out[s].append({
                "year":2025+y,
                "net": round(random.randint(10000,20000)*factor,2)
            })
    return out
```

**IA explicativa** – `backend/app/services/ai_explainer.py`
```python
EXPLANATIONS={
    "Usar factoring":"El flujo proyectado es negativo en los próximos 60 días.",
    "Invertir excedentes":"Se proyecta liquidez positiva sostenida.",
    "Aumentar caja de seguridad":"Existen riesgos fiscales/regulatorios inminentes."
}

def explain_action(action: str):
    return EXPLANATIONS.get(action,"Acción sugerida basada en análisis AI.")
```

**Workflows por rol** – `backend/app/services/workflow_roles.py`
```python
from app.db.models.workflow_role import WorkflowRole
from sqlalchemy.orm import Session

def assign_role(db: Session, role: str, permissions: dict):
    r=WorkflowRole(role=role,permissions=permissions)
    db.add(r); db.commit(); return r.id

def get_permissions(db: Session, role: str):
    r=db.query(WorkflowRole).filter_by(role=role).first()
    return r.permissions if r else {}
```

---

## 4) API
**Forecast escenarios** – `backend/app/api/v1/forecast_scenarios.py`
```python
from fastapi import APIRouter
from app.services.forecast_scenarios import forecast_scenarios

router=APIRouter()

@router.get("/scenarios")
def scenarios(company_id: int, years: int=3):
    return forecast_scenarios(company_id,years)
```

**IA explicativa** – `backend/app/api/v1/ai_explainer.py`
```python
from fastapi import APIRouter
from app.services.ai_explainer import explain_action

router=APIRouter()

@router.get("/explain")
def explain(action: str):
    return {"action":action,"explanation":explain_action(action)}
```

**Workflows roles** – `backend/app/api/v1/workflow_roles.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflow_roles import assign_role,get_permissions

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/assign")
def assign(role: str, permissions: dict, db: Session = Depends(get_db)):
    return {"id": assign_role(db,role,permissions)}

@router.get("/permissions")
def permissions(role: str, db: Session = Depends(get_db)):
    return get_permissions(db,role)
```

---

## 5) UI Next.js
- `/forecast/scenarios`: gráfico comparativo optimista/base/pesimista.
- `/ai/explainer`: explicación de acción IA.
- `/workflows/roles`: asignar roles y ver permisos.
- `/executive/panel`: panel único con forecast + IA + workflows.

**Componentes**
- `ScenarioChart.tsx`: gráfico 3 líneas comparativas.
- `AIExplanation.tsx`: texto con justificación.
- `WorkflowRoles.tsx`: formulario roles/permissions.
- `ExecutivePanel.tsx`: vista integrada forecast/IA/workflows.

---

## 6) Integración OFITEC
- **Forecast escenarios**: completa visión pesimista/base/optimista.
- **IA explicativa**: conecta recomendador IA con justificación.
- **Roles workflows**: asegura jerarquía corporativa.
- **Panel ejecutivo único**: simplifica reporting al directorio.

---

## 7) Checklist Sprint 37-38
- [ ] Migración 0019 aplicada.
- [ ] Forecast multi-escenarios generado.
- [ ] IA explicativa integrada.
- [ ] Roles workflows configurados.
- [ ] Panel ejecutivo desplegado.
- [ ] Tests Pytest de escenarios, IA y workflows.

---

## 8) Próximos pasos (Sprint 39+)
- Forecast combinado multi-escenario IFRS+tributos.
- IA recomendadora explicativa con simulaciones.
- Workflows multinivel (varios aprobadores).
- Panel ejecutivo con KPIs visuales dinámicos.

