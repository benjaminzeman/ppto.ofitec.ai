# OFITEC · Presupuestos/Mediciones – Sprint 51-52

Este Sprint se enfoca en **resiliencia y visión comparativa global**: simulaciones de estrés, IA predictiva regulatoria, workflows multinivel y KPIs comparativos entre grupos de empresas.

---

## 0) Objetivos
- **Simulaciones de estrés**: escenarios extremos (crisis de liquidez, variación FX drástica, alzas tributarias).
- **IA predictiva regulatoria**: anticipar impacto de nuevas normas.
- **Workflows multinivel globales**: pasos jerárquicos entre empresas y niveles directivos.
- **KPIs comparativos**: benchmarking entre grupos de empresas.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0026_stress_ai_reg_workflows_kpis_comp.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0026_stress_ai_reg_workflows_kpis_comp"
down_revision = "0025_probabilistic_global_ai_workflows_realtime"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "stress_tests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer),
        sa.Column("scenario", sa.String()),
        sa.Column("impact", sa.JSON()),
    )

def downgrade():
    op.drop_table("stress_tests")
```

---

## 2) Modelos
**`backend/app/db/models/stress_test.py`**
```python
from sqlalchemy import Column, Integer, String, JSON
from app.db.base import Base

class StressTest(Base):
    __tablename__ = "stress_tests"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer)
    scenario = Column(String)
    impact = Column(JSON)
```

---

## 3) Servicios
**Simulaciones de estrés** – `backend/app/services/stress_tests.py`
```python
import random

SCENARIOS=["crisis liquidez","shock FX","alza impuestos"]

def run_stress(company_id: int):
    scenario=random.choice(SCENARIOS)
    impact={"cash":random.randint(-50000,-10000),"fx":random.uniform(700,1000)}
    return {"company_id":company_id,"scenario":scenario,"impact":impact}
```

**IA regulatoria** – `backend/app/services/ai_regulatory.py`
```python
import random

NORMS=["Ley IVA","Reforma Renta","Norma IFRS"]


def predict_regulatory():
    norm=random.choice(NORMS)
    return {"norm":norm,"impact":f"Impacto proyectado de {norm} sobre cashflow."}
```

**Workflows multinivel globales** – `backend/app/services/workflows_global.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def global_steps(db: Session, group_id: int):
    steps=db.query(WorkflowStep).filter_by(status="pending").all()
    return [{"note_id":s.note_id,"role":s.role,"order":s.order,"company":group_id} for s in steps]
```

**KPIs comparativos** – `backend/app/services/kpis_comparative.py`
```python
import random

KPI_LIST=["Margen Neto","Ebitda","Cash Flow"]

def compare_kpis(groups: list):
    return {g:[{"kpi":k,"value":round(random.uniform(0.5,5.0),2)} for k in KPI_LIST] for g in groups}
```

---

## 4) API
**Stress tests** – `backend/app/api/v1/stress_tests.py`
```python
from fastapi import APIRouter
from app.services.stress_tests import run_stress

router=APIRouter()

@router.get("/stress")
def stress(company_id: int):
    return run_stress(company_id)
```

**IA regulatoria** – `backend/app/api/v1/ai_regulatory.py`
```python
from fastapi import APIRouter
from app.services.ai_regulatory import predict_regulatory

router=APIRouter()

@router.get("/predict")
def predict():
    return predict_regulatory()
```

**Workflows globales** – `backend/app/api/v1/workflows_global.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_global import global_steps

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/steps")
def steps(group_id: int, db: Session = Depends(get_db)):
    return global_steps(db,group_id)
```

**KPIs comparativos** – `backend/app/api/v1/kpis_comparative.py`
```python
from fastapi import APIRouter
from app.services.kpis_comparative import compare_kpis

router=APIRouter()

@router.post("/compare")
def compare(groups: list):
    return compare_kpis(groups)
```

---

## 5) UI Next.js
- `/stress`: lanzar simulaciones.
- `/ai/regulatory`: predicciones de normas.
- `/workflows/global`: ver pasos multinivel.
- `/kpis/comparative`: benchmarking entre grupos.

**Componentes**
- `StressSimulator.tsx`
- `RegulatoryPrediction.tsx`
- `GlobalWorkflow.tsx`
- `ComparativeKPIs.tsx`

---

## 6) Integración OFITEC
- Estrés financiero integrado en forecast.
- IA regulatoria vinculada a escenarios.
- Workflows jerárquicos multi-empresa.
- KPIs comparativos para estrategia.

---

## 7) Checklist Sprint 51-52
- [ ] Migración 0026 aplicada.
- [ ] Stress tests activos.
- [ ] IA regulatoria en marcha.
- [ ] Workflows globales funcionando.
- [ ] KPIs comparativos desplegados.
- [ ] UI completa integrada.
- [ ] Tests Pytest listos.

---

## 8) Próximos pasos (Sprint 53+)
- Forecast resiliente multi-año.
- IA generativa de mitigación de riesgos.
- Workflows globales auto-optimizados.
- KPIs narrativos (explicaciones automáticas).

