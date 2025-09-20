# OFITEC · Presupuestos/Mediciones – Sprint 59-60

Este Sprint impulsa la **interactividad y la inteligencia colectiva**: simulaciones interactivas globales, IA multimodal avanzada, workflows colaborativos con inteligencia colectiva y KPIs con alertas proactivas.

---

## 0) Objetivos
- **Simulaciones interactivas**: forecast donde el usuario ajusta parámetros en tiempo real.
- **IA multimodal avanzada**: explicaciones que combinan texto, visuales y datos históricos.
- **Workflows con inteligencia colectiva**: decisiones optimizadas por múltiples usuarios y roles.
- **KPIs con alertas proactivas**: métricas vivas que disparan notificaciones inmediatas.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0030_interactive_simulations_ai_multimodal_collective_kpis_alerts.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0030_interactive_simulations_ai_multimodal_collective_kpis_alerts"
down_revision = "0029_hybrid_forecast_multimodal_workflows_actionable_kpis"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "kpi_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kpi", sa.String()),
        sa.Column("threshold", sa.Float()),
        sa.Column("status", sa.String()),
    )

def downgrade():
    op.drop_table("kpi_alerts")
```

---

## 2) Modelos
**`backend/app/db/models/kpi_alert.py`**
```python
from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class KPIAlert(Base):
    __tablename__ = "kpi_alerts"
    id = Column(Integer, primary_key=True)
    kpi = Column(String)
    threshold = Column(Float)
    status = Column(String)
```

---

## 3) Servicios
**Simulaciones interactivas** – `backend/app/services/simulations_interactive.py`
```python
import random

def run_interactive(params: dict):
    cash=random.gauss(params.get("cash",50000),5000)
    fx=params.get("fx",850)+random.uniform(-50,50)
    return {"cash":cash,"fx":fx,"params":params}
```

**IA multimodal avanzada** – `backend/app/services/ai_multimodal_adv.py`
```python
import random

VISUALS=["heatmap","gráfico 3D","timeline"]

def generate_multimodal_adv(company_id: int):
    visual=random.choice(VISUALS)
    return {"company_id":company_id,"narrative":f"Explicación avanzada con {visual}."}
```

**Workflows inteligencia colectiva** – `backend/app/services/workflows_collective.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def collective_decision(db: Session, note_id: int, votes: dict):
    # votos = {"Aprobado":10,"Rechazado":2}
    decision=max(votes,key=votes.get)
    return {"note_id":note_id,"decision":decision,"votes":votes}
```

**KPIs alertas proactivas** – `backend/app/services/kpis_alerts.py`
```python
import random

KPI_LIST=["Liquidez","Ebitda","DSCR"]

def check_alerts(thresholds: dict):
    alerts=[]
    for k in KPI_LIST:
        val=random.uniform(0.0,5.0)
        if val<thresholds.get(k,1.0):
            alerts.append({"kpi":k,"value":val,"alert":"ON"})
    return alerts
```

---

## 4) API
**Simulaciones interactivas** – `backend/app/api/v1/simulations_interactive.py`
```python
from fastapi import APIRouter
from app.services.simulations_interactive import run_interactive

router=APIRouter()

@router.post("/interactive")
def interactive(params: dict):
    return run_interactive(params)
```

**IA multimodal avanzada** – `backend/app/api/v1/ai_multimodal_adv.py`
```python
from fastapi import APIRouter
from app.services.ai_multimodal_adv import generate_multimodal_adv

router=APIRouter()

@router.get("/multimodal-adv")
def multimodal_adv(company_id: int):
    return generate_multimodal_adv(company_id)
```

**Workflows colectiva** – `backend/app/api/v1/workflows_collective.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_collective import collective_decision

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/decision")
def decision(note_id: int, votes: dict, db: Session = Depends(get_db)):
    return collective_decision(db,note_id,votes)
```

**KPIs alertas** – `backend/app/api/v1/kpis_alerts.py`
```python
from fastapi import APIRouter
from app.services.kpis_alerts import check_alerts

router=APIRouter()

@router.post("/check")
def check(thresholds: dict):
    return check_alerts(thresholds)
```

---

## 5) UI Next.js
- `/forecast/interactive`: simulador en vivo con sliders.
- `/ai/multimodal-adv`: panel multimodal avanzado.
- `/workflows/collective`: votación colaborativa.
- `/kpis/alerts`: dashboard con alertas activas.

**Componentes**
- `InteractiveSimulator.tsx`
- `AdvancedMultimodal.tsx`
- `CollectiveWorkflow.tsx`
- `AlertKPIs.tsx`

---

## 6) Integración OFITEC
- Simulaciones ajustables en dashboards.
- Explicaciones multimodales enriquecidas.
- Workflows colectivos distribuidos.
- KPIs con alertas en tiempo real.

---

## 7) Checklist Sprint 59-60
- [ ] Migración 0030 aplicada.
- [ ] Simulaciones interactivas listas.
- [ ] IA multimodal avanzada desplegada.
- [ ] Workflows colectivos activos.
- [ ] Alertas de KPIs en UI.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 61+)
- Forecast con IA adaptativa en tiempo real.
- Narrativas multimodales interactivas.
- Workflows con feedback loop.
- KPIs gamificados (metas y logros).

