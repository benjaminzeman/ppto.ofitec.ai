# OFITEC · Presupuestos/Mediciones – Sprint 55-56

Este Sprint introduce **profundidad analítica y storytelling visual**: forecast resiliente multi-escenario, IA narrativa extensa, workflows con auto-aprendizaje y KPIs presentados con visualización narrativa.

---

## 0) Objetivos
- **Sensibilidad multi-escenario**: análisis simultáneo de escenarios extremos y variaciones.
- **IA narrativa larga**: generar reportes ejecutivos con storytelling extenso.
- **Workflows auto-aprendizaje**: mejorar rutas de aprobación basadas en datos históricos.
- **KPIs storytelling visual**: visualizaciones que mezclan datos y texto explicativo.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0028_multi_scenario_ai_narrative_workflows_storytelling.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0028_multi_scenario_ai_narrative_workflows_storytelling"
down_revision = "0027_resilient_forecast_ai_risks_workflows_kpis_narrative"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "scenario_sensitivities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer),
        sa.Column("scenarios", sa.JSON()),
        sa.Column("results", sa.JSON()),
    )

def downgrade():
    op.drop_table("scenario_sensitivities")
```

---

## 2) Modelos
**`backend/app/db/models/scenario_sensitivity.py`**
```python
from sqlalchemy import Column, Integer, JSON
from app.db.base import Base

class ScenarioSensitivity(Base):
    __tablename__ = "scenario_sensitivities"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer)
    scenarios = Column(JSON)
    results = Column(JSON)
```

---

## 3) Servicios
**Sensibilidad multi-escenario** – `backend/app/services/scenario_sensitivity.py`
```python
import random

def run_scenarios(company_id: int, scenarios: list):
    results={}
    for s in scenarios:
        results[s]={"impact":random.randint(-50000,50000)}
    return {"company_id":company_id,"scenarios":results}
```

**IA narrativa larga** – `backend/app/services/ai_long_narrative.py`
```python
import random

SECTIONS=["Liquidez","Tributación","FX","Inversiones"]

def generate_long_narrative(company_id: int):
    return "\n".join([f"Sección {s}: análisis detallado y proyección futura." for s in SECTIONS])
```

**Workflows auto-aprendizaje** – `backend/app/services/workflows_learning.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def learn_from_history(db: Session, company_id: int):
    steps=db.query(WorkflowStep).all()
    approved=sum(1 for s in steps if s.status=="approved")
    pending=sum(1 for s in steps if s.status=="pending")
    return {"approved":approved,"pending":pending,"suggestion":"reducir pasos" if approved>pending else "mantener"}
```

**KPIs storytelling visual** – `backend/app/services/kpis_storytelling.py`
```python
import random

KPI_LIST=["Margen Neto","Ebitda","Cash Flow"]

def storytelling_kpis():
    return [{"kpi":k,"value":round(random.uniform(0.5,5.0),2),"narrative":f"El indicador {k} muestra tendencia positiva."} for k in KPI_LIST]
```

---

## 4) API
**Sensibilidad escenarios** – `backend/app/api/v1/scenario_sensitivity.py`
```python
from fastapi import APIRouter
from app.services.scenario_sensitivity import run_scenarios

router=APIRouter()

@router.post("/sensitivity")
def sensitivity(company_id: int, scenarios: list):
    return run_scenarios(company_id,scenarios)
```

**IA narrativa larga** – `backend/app/api/v1/ai_long_narrative.py`
```python
from fastapi import APIRouter
from app.services.ai_long_narrative import generate_long_narrative

router=APIRouter()

@router.get("/narrative")
def narrative(company_id: int):
    return {"company_id":company_id,"report":generate_long_narrative(company_id)}
```

**Workflows aprendizaje** – `backend/app/api/v1/workflows_learning.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_learning import learn_from_history

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/learn")
def learn(company_id: int, db: Session = Depends(get_db)):
    return learn_from_history(db,company_id)
```

**KPIs storytelling** – `backend/app/api/v1/kpis_storytelling.py`
```python
from fastapi import APIRouter
from app.services.kpis_storytelling import storytelling_kpis

router=APIRouter()

@router.get("/storytelling")
def storytelling():
    return storytelling_kpis()
```

---

## 5) UI Next.js
- `/forecast/sensitivity`: panel de escenarios comparativos.
- `/ai/narrative-long`: reporte extenso.
- `/workflows/learning`: sugerencias de optimización.
- `/kpis/storytelling`: KPIs con visualización + narrativa.

**Componentes**
- `ScenarioSensitivityChart.tsx`
- `LongNarrativeReport.tsx`
- `WorkflowLearning.tsx`
- `StorytellingKPIs.tsx`

---

## 6) Integración OFITEC
- Sensibilidad extendida unida al forecast resiliente.
- Narrativas largas integradas en reportes PDF.
- Workflows con aprendizaje de historial.
- KPIs storytelling en dashboards.

---

## 7) Checklist Sprint 55-56
- [ ] Migración 0028 aplicada.
- [ ] Escenarios multi-sensibilidad implementados.
- [ ] Narrativa larga generada.
- [ ] Workflows con aprendizaje operativo.
- [ ] KPIs storytelling desplegados.
- [ ] UI integrada.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 57+)
- Forecast con IA híbrida (predictiva + generativa).
- Narrativas multimodales (texto + visual).
- Workflows colaborativos globales.
- KPIs con insights automáticos accionables.

