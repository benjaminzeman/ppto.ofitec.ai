# OFITEC · Presupuestos/Mediciones – Sprint 61-62

Este Sprint busca cerrar la brecha hacia un **sistema adaptativo y gamificado**: forecast con IA en tiempo real, narrativas interactivas, workflows con feedback loop y KPIs con gamificación.

---

## 0) Objetivos
- **Forecast con IA adaptativa**: actualización continua según datos entrantes.
- **Narrativas interactivas**: reportes dinámicos con participación del usuario.
- **Workflows con feedback loop**: optimización basada en resultados previos.
- **KPIs gamificados**: métricas presentadas con metas y logros alcanzables.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0031_adaptive_ai_interactive_narratives_feedback_kpis_gamified.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0031_adaptive_ai_interactive_narratives_feedback_kpis_gamified"
down_revision = "0030_interactive_simulations_ai_multimodal_collective_kpis_alerts"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "gamified_kpis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kpi", sa.String()),
        sa.Column("value", sa.Float()),
        sa.Column("goal", sa.Float()),
        sa.Column("status", sa.String()),
    )

def downgrade():
    op.drop_table("gamified_kpis")
```

---

## 2) Modelos
**`backend/app/db/models/gamified_kpi.py`**
```python
from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class GamifiedKPI(Base):
    __tablename__ = "gamified_kpis"
    id = Column(Integer, primary_key=True)
    kpi = Column(String)
    value = Column(Float)
    goal = Column(Float)
    status = Column(String)
```

---

## 3) Servicios
**Forecast adaptativo** – `backend/app/services/forecast_adaptive.py`
```python
import random

def adaptive_forecast(company_id: int, new_data: dict):
    base=random.gauss(50000,5000)
    adj=base+new_data.get("adjustment",0)
    return {"company_id":company_id,"forecast":adj,"updated":True}
```

**Narrativas interactivas** – `backend/app/services/ai_interactive_narratives.py`
```python

def interactive_narrative(input_text: str):
    return {"narrative":f"Reporte interactivo ajustado con entrada del usuario: {input_text}"}
```

**Workflows feedback loop** – `backend/app/services/workflows_feedback.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def feedback_optimize(db: Session, company_id: int, success: bool):
    steps=db.query(WorkflowStep).filter_by(status="pending").all()
    if success:
        for s in steps:
            s.order=max(1,s.order-1)
    else:
        for s in steps:
            s.order+=1
    db.commit()
    return {"optimized_steps":len(steps)}
```

**KPIs gamificados** – `backend/app/services/kpis_gamified.py`
```python
import random

KPI_LIST=["Liquidez","Ebitda","Cash Flow"]

def gamified_kpis():
    out=[]
    for k in KPI_LIST:
        val=random.uniform(0.5,5.0)
        goal=3.0
        status="OK" if val>=goal else "En progreso"
        out.append({"kpi":k,"value":val,"goal":goal,"status":status})
    return out
```

---

## 4) API
**Forecast adaptativo** – `backend/app/api/v1/forecast_adaptive.py`
```python
from fastapi import APIRouter
from app.services.forecast_adaptive import adaptive_forecast

router=APIRouter()

@router.post("/adaptive")
def adaptive(company_id: int, new_data: dict):
    return adaptive_forecast(company_id,new_data)
```

**Narrativas interactivas** – `backend/app/api/v1/ai_interactive_narratives.py`
```python
from fastapi import APIRouter
from app.services.ai_interactive_narratives import interactive_narrative

router=APIRouter()

@router.post("/interactive")
def interactive(input_text: str):
    return interactive_narrative(input_text)
```

**Workflows feedback loop** – `backend/app/api/v1/workflows_feedback.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_feedback import feedback_optimize

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/feedback")
def feedback(company_id: int, success: bool, db: Session = Depends(get_db)):
    return feedback_optimize(db,company_id,success)
```

**KPIs gamificados** – `backend/app/api/v1/kpis_gamified.py`
```python
from fastapi import APIRouter
from app.services.kpis_gamified import gamified_kpis

router=APIRouter()

@router.get("/gamified")
def gamified():
    return gamified_kpis()
```

---

## 5) UI Next.js
- `/forecast/adaptive`: forecast que reacciona en tiempo real.
- `/ai/narrative-interactive`: reportes interactivos.
- `/workflows/feedback`: panel con feedback loop.
- `/kpis/gamified`: dashboard gamificado.

**Componentes**
- `AdaptiveForecast.tsx`
- `InteractiveNarrative.tsx`
- `FeedbackWorkflows.tsx`
- `GamifiedKPIs.tsx`

---

## 6) Integración OFITEC
- Forecast adaptativo conectado a feeds en vivo.
- Narrativas enriquecidas con inputs de usuario.
- Workflows que aprenden de éxitos y errores.
- KPIs con gamificación para motivar equipos.

---

## 7) Checklist Sprint 61-62
- [ ] Migración 0031 aplicada.
- [ ] Forecast adaptativo operativo.
- [ ] Narrativas interactivas activas.
- [ ] Workflows con feedback funcionando.
- [ ] KPIs gamificados desplegados.
- [ ] UI integrada.
- [ ] Tests listos.

---

## 8) Próximos pasos (Sprint 63+)
- Forecast adaptativo con auto-sintonización.
- Narrativas personalizadas por usuario.
- Workflows con reputación de roles.
- KPIs con recompensas dinámicas.

