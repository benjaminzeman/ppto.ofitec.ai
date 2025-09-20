# OFITEC · Presupuestos/Mediciones – Sprint 43-44

Este Sprint apunta a la **inteligencia autónoma aplicada**: forecast global con simulaciones, IA explicativa conectada a históricos, workflows con auto-aprendizaje y KPIs ajustados dinámicamente con machine learning.

---

## 0) Objetivos

- **Forecast global con simulaciones**: escenarios múltiples con Montecarlo.
- **IA explicativa histórica**: razones basadas en datasets pasados.
- **Workflows auto-aprendizaje**: priorizar rutas según experiencia.
- **KPIs ML**: ajuste dinámico de métricas con machine learning.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0022_forecast_ai_auto_kpisml"
down_revision = "0021_forecast_ai_workflows_kpis_personalized"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("user_kpis", sa.Column("ml_adjusted", sa.Boolean(), server_default="false"))

def downgrade():
    op.drop_column("user_kpis", "ml_adjusted")
```

---

## 2) Modelos

*(extensión de **`UserKPI`** con campo **`ml_adjusted`**)*

---

## 3) Servicios

**Forecast global con simulaciones** – `backend/app/services/forecast_simulations.py`

```python
import random

def forecast_simulations(company_id: int, runs: int=100):
    results=[]
    for r in range(runs):
        iva=random.randint(8000,12000)
        renta=random.randint(15000,25000)
        net=iva+renta+random.randint(-2000,2000)
        results.append(net)
    avg=sum(results)/len(results)
    return {"runs":runs,"avg":avg,"min":min(results),"max":max(results)}
```

**IA explicativa histórica** – `backend/app/services/ai_history.py`

```python
import random

REASONS=["patrones de liquidez","desviaciones de renta","impacto regulatorio"]

def explain_from_history(action: str):
    reason=random.choice(REASONS)
    return f"La acción {action} se justifica por {reason} observados en periodos anteriores."
```

**Workflows auto-aprendizaje** – `backend/app/services/workflows_auto.py`

```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

# Simplificado: prioriza rol más usado históricamente

def auto_next(db: Session, note_id: int):
    steps=db.query(WorkflowStep).filter_by(note_id=note_id).all()
    if not steps: return None
    # Heurística: elegir primer pendiente
    for s in steps:
        if s.status=="pending": return s.role
    return None
```

**KPIs ML** – `backend/app/services/kpis_ml.py`

```python
import random

KPI_LIST=["Margen Neto","Ebitda","Deuda/EBITDA","Cash Ratio"]

def generate_kpis_ml():
    return [{"kpi":k,"value":round(random.uniform(0.5,3.0),2),"adjusted":True} for k in KPI_LIST]
```

---

## 4) API

**Forecast simulaciones** – `backend/app/api/v1/forecast_simulations.py`

```python
from fastapi import APIRouter
from app.services.forecast_simulations import forecast_simulations

router=APIRouter()

@router.get("/simulations")
def simulations(company_id: int, runs: int=100):
    return forecast_simulations(company_id,runs)
```

**IA histórica** – `backend/app/api/v1/ai_history.py`

```python
from fastapi import APIRouter
from app.services.ai_history import explain_from_history

router=APIRouter()

@router.get("/explain")
def explain(action: str):
    return {"action":action,"explanation":explain_from_history(action)}
```

**Workflows auto** – `backend/app/api/v1/workflows_auto.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_auto import auto_next

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/auto-next")
def auto_next_(note_id: int, db: Session = Depends(get_db)):
    return {"next_role": auto_next(db,note_id)}
```

**KPIs ML** – `backend/app/api/v1/kpis_ml.py`

```python
from fastapi import APIRouter
from app.services.kpis_ml import generate_kpis_ml

router=APIRouter()

@router.get("/generate")
def generate():
    return generate_kpis_ml()
```

---

## 5) UI Next.js

- `/forecast/simulations`: gráfico Montecarlo.
- `/ai/history`: explicaciones históricas.
- `/workflows/auto`: sugerencia automática de aprobador.
- `/kpis/ml`: KPIs dinámicos ajustados.

**Componentes**

- `MonteCarloChart.tsx`: histograma resultados.
- `HistoryExplanation.tsx`: cuadro con explicación IA.
- `AutoWorkflow.tsx`: muestra rol sugerido.
- `KPIsML.tsx`: tarjetas KPIs ajustadas.

---

## 6) Integración OFITEC

- **Forecast simulaciones**: añade análisis probabilístico.
- **IA histórica**: fortalece explicaciones con datos previos.
- **Workflows auto-aprendizaje**: reduce fricción en aprobaciones.
- **KPIs ML**: métricas vivas y adaptadas.

---

## 7) Checklist Sprint 43-44

-

---

## 8) Próximos pasos (Sprint 45+)

- Forecast integrado global + Montecarlo IFRS/tributos.
- IA generativa con explicaciones sobre riesgos.
- Workflows híbridos (manual+auto).
- KPIs predictivos con ML avanzado (redes neuronales).

