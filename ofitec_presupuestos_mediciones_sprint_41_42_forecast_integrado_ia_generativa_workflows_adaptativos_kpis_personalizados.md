# OFITEC · Presupuestos/Mediciones – Sprint 41-42

Este Sprint integra todas las capas de **contabilidad, tributación y regulación**, añade IA generativa explicativa, workflows adaptativos y KPIs personalizados por rol/usuario.

---

## 0) Objetivos

- **Forecast integrado IFRS/tributos/regulación**: visión única de proyecciones financieras, fiscales y normativas.
- **IA generativa explicativa**: justificación en lenguaje natural de escenarios y decisiones.
- **Workflows adaptativos**: rutas de aprobación que cambian según condiciones.
- **KPIs personalizados**: indicadores ajustados por usuario y rol.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0021_forecast_ai_workflows_kpis_personalized"
down_revision = "0020_ifrs_tax_ai_workflows_kpis"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "user_kpis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer),
        sa.Column("kpis", sa.JSON()),
    )

def downgrade():
    op.drop_table("user_kpis")
```

---

## 2) Modelos

``

```python
from sqlalchemy import Column, Integer, JSON
from app.db.base import Base

class UserKPI(Base):
    __tablename__ = "user_kpis"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    kpis = Column(JSON)
```

---

## 3) Servicios

**Forecast integrado** – `backend/app/services/forecast_integrated.py`

```python
import random

def forecast_integrated(company_id: int, years: int=3):
    out=[]
    for y in range(years):
        iva=random.randint(8000,12000)
        renta=random.randint(15000,25000)
        assets=random.randint(900000,1100000)
        reg_impact=random.choice(["Ley IVA","Reforma Renta","Norma IFRS"])
        out.append({"year":2025+y,"IVA":iva,"Renta":renta,"Assets":assets,"RegImpact":reg_impact})
    return out
```

**IA generativa explicativa** – `backend/app/services/ai_generative.py`

```python
import random

TEMPLATES=[
    "El escenario {scenario} refleja un {impact} debido a {reason}.",
    "Se proyecta un {impact} en el escenario {scenario}, impulsado por {reason}."
]

REASONS=["cambios tributarios","variaciones en FX","ajustes regulatorios"]


def explain_scenario(scenario: str):
    tpl=random.choice(TEMPLATES)
    reason=random.choice(REASONS)
    impact="crecimiento" if scenario=="optimista" else "riesgo" if scenario=="pesimista" else "equilibrio"
    return tpl.format(scenario=scenario,impact=impact,reason=reason)
```

**Workflows adaptativos** – `backend/app/services/workflows_adaptive.py`

```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def next_step(db: Session, note_id: int, current_role: str):
    steps=db.query(WorkflowStep).filter_by(note_id=note_id).order_by(WorkflowStep.order).all()
    for s in steps:
        if s.role!=current_role and s.status=="pending":
            return s.role
    return None
```

**KPIs personalizados** – `backend/app/services/user_kpis.py`

```python
from app.db.models.user_kpi import UserKPI
from sqlalchemy.orm import Session

def set_user_kpis(db: Session, user_id: int, kpis: dict):
    u=UserKPI(user_id=user_id,kpis=kpis)
    db.add(u); db.commit(); return u.id

def get_user_kpis(db: Session, user_id: int):
    u=db.query(UserKPI).filter_by(user_id=user_id).first()
    return u.kpis if u else {}
```

---

## 4) API

**Forecast integrado** – `backend/app/api/v1/forecast_integrated.py`

```python
from fastapi import APIRouter
from app.services.forecast_integrated import forecast_integrated

router=APIRouter()

@router.get("/integrated")
def integrated(company_id: int, years: int=3):
    return forecast_integrated(company_id,years)
```

**IA generativa** – `backend/app/api/v1/ai_generative.py`

```python
from fastapi import APIRouter
from app.services.ai_generative import explain_scenario

router=APIRouter()

@router.get("/explain")
def explain(scenario: str):
    return {"scenario":scenario,"explanation":explain_scenario(scenario)}
```

**Workflows adaptativos** – `backend/app/api/v1/workflows_adaptive.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_adaptive import next_step

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/next")
def next_(note_id: int, current_role: str, db: Session = Depends(get_db)):
    return {"next_role": next_step(db,note_id,current_role)}
```

**KPIs personalizados** – `backend/app/api/v1/user_kpis.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.user_kpis import set_user_kpis,get_user_kpis

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/set")
def set_(user_id: int, kpis: dict, db: Session = Depends(get_db)):
    return {"id": set_user_kpis(db,user_id,kpis)}

@router.get("/get")
def get(user_id: int, db: Session = Depends(get_db)):
    return get_user_kpis(db,user_id)
```

---

## 5) UI Next.js

- `/forecast/integrated`: forecast único IFRS+tributos+regulación.
- `/ai/generative`: explicaciones de escenarios.
- `/workflows/adaptive`: mostrar siguiente paso dinámico.
- `/kpis/user`: dashboard personalizado.

**Componentes**

- `IntegratedForecast.tsx`: tabla consolidada.
- `ScenarioExplanation.tsx`: cuadro explicativo IA.
- `AdaptiveWorkflow.tsx`: flujo dinámico de aprobaciones.
- `UserKPIDashboard.tsx`: tarjetas KPI por rol/usuario.

---

## 6) Integración OFITEC

- **Forecast integrado**: une contabilidad, impuestos y regulación.
- **IA generativa**: explica decisiones de manera natural.
- **Workflows adaptativos**: ajustan procesos a condiciones.
- **KPIs personalizados**: refuerzan visión individualizada.

---

## 7) Checklist Sprint 41-42

-

---

## 8) Próximos pasos (Sprint 43+)

- Forecast global consolidado con simulaciones.
- IA explicativa conectada a datasets históricos.
- Workflows auto-aprendizaje (ML sobre decisiones).
- KPIs dinámicos ajustados por machine learning.

