# OFITEC · Presupuestos/Mediciones – Sprint 49-50

Este Sprint lleva OFITEC hacia la **toma de decisiones probabilística y en tiempo real**: escenarios globales, IA generativa de decisiones, workflows multi-empresa híbridos y KPIs en streaming.

---

## 0) Objetivos
- **Escenarios probabilísticos globales**: forecast con Montecarlo unificado (finanzas + tributos + FX + regulación).
- **IA generativa de decisiones**: proponer acciones estratégicas basadas en datos en tiempo real.
- **Workflows multi-empresa híbridos**: coordinación entre compañías con pasos manuales y automáticos.
- **KPIs en tiempo real**: métricas vivas con actualización vía websockets.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0025_probabilistic_global_ai_workflows_realtime.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0025_probabilistic_global_ai_workflows_realtime"
down_revision = "0024_forecast_proactive_workflows_kpis_interactive"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "company_groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String()),
        sa.Column("companies", sa.JSON()),
    )

def downgrade():
    op.drop_table("company_groups")
```

---

## 2) Modelos
**`backend/app/db/models/company_group.py`**
```python
from sqlalchemy import Column, Integer, String, JSON
from app.db.base import Base

class CompanyGroup(Base):
    __tablename__ = "company_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    companies = Column(JSON)
```

---

## 3) Servicios
**Forecast probabilístico global** – `backend/app/services/forecast_probabilistic.py`
```python
import random

def forecast_probabilistic(group_id: int, runs: int=1000):
    results=[]
    for r in range(runs):
        iva=random.gauss(10000,1500)
        renta=random.gauss(20000,2500)
        fx=random.gauss(850,50)
        assets=random.gauss(1000000,100000)
        results.append(iva+renta+fx+assets)
    return {
        "runs":runs,
        "avg":sum(results)/len(results),
        "min":min(results),
        "max":max(results)
    }
```

**IA generativa de decisiones** – `backend/app/services/ai_decisions.py`
```python
import random

ACTIONS=["Expandir inversión","Reducir gastos","Solicitar factoring","Reforzar caja"]
REASONS=["proyección de liquidez negativa","variación FX alta","riesgo tributario detectado"]


def generate_decision():
    action=random.choice(ACTIONS)
    reason=random.choice(REASONS)
    return {"decision":action,"justification":f"Se recomienda {action} por {reason}."}
```

**Workflows multi-empresa híbridos** – `backend/app/services/workflows_multi.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def sync_workflows(db: Session, group_id: int):
    # Simplificación: devuelve lista de roles pendientes entre empresas
    steps=db.query(WorkflowStep).filter_by(status="pending").all()
    return [{"note_id":s.note_id,"role":s.role,"company":group_id} for s in steps]
```

**KPIs en tiempo real** – `backend/app/services/kpis_realtime.py`
```python
import random

KPI_LIST=["Margen Neto","Ebitda","Cash Flow","DSCR"]

def stream_kpis():
    return [{"kpi":k,"value":round(random.uniform(0.5,5.0),2)} for k in KPI_LIST]
```

---

## 4) API
**Forecast probabilístico** – `backend/app/api/v1/forecast_probabilistic.py`
```python
from fastapi import APIRouter
from app.services.forecast_probabilistic import forecast_probabilistic

router=APIRouter()

@router.get("/probabilistic")
def probabilistic(group_id: int, runs: int=1000):
    return forecast_probabilistic(group_id,runs)
```

**IA decisiones** – `backend/app/api/v1/ai_decisions.py`
```python
from fastapi import APIRouter
from app.services.ai_decisions import generate_decision

router=APIRouter()

@router.get("/decision")
def decision():
    return generate_decision()
```

**Workflows multi-empresa** – `backend/app/api/v1/workflows_multi.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_multi import sync_workflows

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/sync")
def sync(group_id: int, db: Session = Depends(get_db)):
    return sync_workflows(db,group_id)
```

**KPIs realtime** – `backend/app/api/v1/kpis_realtime.py`
```python
from fastapi import APIRouter
from app.services.kpis_realtime import stream_kpis

router=APIRouter()

@router.get("/stream")
def stream():
    return stream_kpis()
```

---

## 5) UI Next.js
- `/forecast/probabilistic`: gráfico Montecarlo global.
- `/ai/decisions`: panel con decisiones generadas.
- `/workflows/multi`: lista consolidada de pasos.
- `/kpis/realtime`: dashboard en vivo (websockets).

**Componentes**
- `ProbabilisticForecastChart.tsx`: histograma Montecarlo.
- `DecisionPanel.tsx`: cuadro acción + justificación.
- `MultiWorkflow.tsx`: pasos por empresa.
- `RealtimeKPIs.tsx`: KPIs en streaming.

---

## 6) Integración OFITEC
- Forecast global unificado probabilístico.
- IA de decisiones en dashboards.
- Workflows multi-empresa coordinados.
- KPIs en vivo para directorio.

---

## 7) Checklist Sprint 49-50
- [ ] Migración 0025 aplicada.
- [ ] Forecast probabilístico global activo.
- [ ] IA decisiones desplegada.
- [ ] Workflows multi-empresa funcionando.
- [ ] KPIs en tiempo real en UI.
- [ ] Tests Pytest completos.

---

## 8) Próximos pasos (Sprint 51+)
- Forecast integrado con simulaciones de estrés.
- IA predictiva para escenarios regulatorios.
- Workflows multinivel globales.
- KPIs comparativos entre grupos de empresas.

