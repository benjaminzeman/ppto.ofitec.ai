# OFITEC · Presupuestos/Mediciones – Sprint 57-58

Este Sprint busca integrar **IA híbrida y narrativas multimodales**: forecast híbrido (predictivo + generativo), narrativas enriquecidas con texto e imágenes, workflows colaborativos globales y KPIs con insights accionables.

---

## 0) Objetivos
- **Forecast híbrido IA**: combinar modelos predictivos (ML) con generativos (IA explicativa).
- **Narrativas multimodales**: generar reportes con texto, tablas y visualizaciones.
- **Workflows colaborativos globales**: coordinar aprobaciones y decisiones entre grupos de empresas distribuidas.
- **KPIs accionables**: métricas que incluyen insight y recomendación de acción.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0029_hybrid_forecast_multimodal_workflows_actionable_kpis.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0029_hybrid_forecast_multimodal_workflows_actionable_kpis"
down_revision = "0028_multi_scenario_ai_narrative_workflows_storytelling"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "actionable_kpis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kpi", sa.String()),
        sa.Column("value", sa.Float()),
        sa.Column("insight", sa.Text()),
        sa.Column("action", sa.Text()),
    )

def downgrade():
    op.drop_table("actionable_kpis")
```

---

## 2) Modelos
**`backend/app/db/models/actionable_kpi.py`**
```python
from sqlalchemy import Column, Integer, String, Float, Text
from app.db.base import Base

class ActionableKPI(Base):
    __tablename__ = "actionable_kpis"
    id = Column(Integer, primary_key=True)
    kpi = Column(String)
    value = Column(Float)
    insight = Column(Text)
    action = Column(Text)
```

---

## 3) Servicios
**Forecast híbrido IA** – `backend/app/services/forecast_hybrid.py`
```python
import random

def hybrid_forecast(company_id: int):
    predictive={"cash":random.gauss(50000,5000)}
    generative={"explanation":"La proyección indica resiliencia frente a variaciones FX."}
    return {"company_id":company_id,"predictive":predictive,"generative":generative}
```

**Narrativas multimodales** – `backend/app/services/ai_multimodal.py`
```python
import random

VISUALS=["gráfico de barras","tabla comparativa","línea de tendencia"]

def generate_multimodal(company_id: int):
    visual=random.choice(VISUALS)
    return {"company_id":company_id,"narrative":f"Reporte multimodal con {visual}."}
```

**Workflows colaborativos globales** – `backend/app/services/workflows_collab.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def collab_steps(db: Session, group_id: int):
    steps=db.query(WorkflowStep).filter_by(status="pending").all()
    return [{"note_id":s.note_id,"role":s.role,"company":group_id,"status":s.status} for s in steps]
```

**KPIs accionables** – `backend/app/services/kpis_actionable.py`
```python
import random

KPI_LIST=["Liquidez","Margen","Ebitda"]

ACTIONS=["Aumentar caja","Reducir costos","Diversificar ingresos"]

def actionable_kpis():
    return [{"kpi":k,"value":round(random.uniform(1.0,5.0),2),"insight":f"Insight sobre {k}","action":random.choice(ACTIONS)} for k in KPI_LIST]
```

---

## 4) API
**Forecast híbrido** – `backend/app/api/v1/forecast_hybrid.py`
```python
from fastapi import APIRouter
from app.services.forecast_hybrid import hybrid_forecast

router=APIRouter()

@router.get("/hybrid")
def hybrid(company_id: int):
    return hybrid_forecast(company_id)
```

**Narrativas multimodales** – `backend/app/api/v1/ai_multimodal.py`
```python
from fastapi import APIRouter
from app.services.ai_multimodal import generate_multimodal

router=APIRouter()

@router.get("/multimodal")
def multimodal(company_id: int):
    return generate_multimodal(company_id)
```

**Workflows colaborativos** – `backend/app/api/v1/workflows_collab.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_collab import collab_steps

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/collab")
def collab(group_id: int, db: Session = Depends(get_db)):
    return collab_steps(db,group_id)
```

**KPIs accionables** – `backend/app/api/v1/kpis_actionable.py`
```python
from fastapi import APIRouter
from app.services.kpis_actionable import actionable_kpis

router=APIRouter()

@router.get("/actionable")
def actionable():
    return actionable_kpis()
```

---

## 5) UI Next.js
- `/forecast/hybrid`: vista con predicciones + explicación.
- `/ai/multimodal`: reporte multimodal.
- `/workflows/collab`: lista colaborativa global.
- `/kpis/actionable`: KPIs con acciones sugeridas.

**Componentes**
- `HybridForecastPanel.tsx`
- `MultimodalNarrative.tsx`
- `CollaborativeWorkflow.tsx`
- `ActionableKPIs.tsx`

---

## 6) Integración OFITEC
- Forecast híbrido en dashboards globales.
- Narrativas multimodales en reportes PDF/HTML.
- Workflows colaborativos conectados a grupos.
- KPIs accionables integrados en decisiones.

---

## 7) Checklist Sprint 57-58
- [ ] Migración 0029 aplicada.
- [ ] Forecast híbrido activo.
- [ ] Narrativas multimodales generadas.
- [ ] Workflows colaborativos desplegados.
- [ ] KPIs accionables en UI.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 59+)
- Forecast global con simulaciones interactivas.
- IA multimodal explicativa avanza