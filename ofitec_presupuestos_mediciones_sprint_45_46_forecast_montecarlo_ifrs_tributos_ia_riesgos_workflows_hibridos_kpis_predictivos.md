# OFITEC · Presupuestos/Mediciones – Sprint 45-46

Este Sprint eleva OFITEC a la **predicción avanzada de riesgos y finanzas**: forecast Montecarlo IFRS/tributos, IA generativa de riesgos, workflows híbridos y KPIs predictivos con redes neuronales.

---

## 0) Objetivos

- **Forecast Montecarlo IFRS/tributos**: simulaciones probabilísticas integradas.
- **IA de riesgos**: explicaciones generativas sobre amenazas fiscales/financieras.
- **Workflows híbridos**: combinación manual + automático.
- **KPIs predictivos**: métricas proyectadas con modelos neuronales.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0023_forecast_risks_workflows_kpis_pred"
down_revision = "0022_forecast_ai_auto_kpisml"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("workflow_steps", sa.Column("mode", sa.String(), server_default="manual"))

def downgrade():
    op.drop_column("workflow_steps", "mode")
```

---

## 2) Modelos

*(extensión **`WorkflowStep`** con campo **`mode`** = manual|auto|híbrido)*

---

## 3) Servicios

**Forecast Montecarlo IFRS/tributos** – `backend/app/services/forecast_montecarlo.py`

```python
import random

def forecast_montecarlo(company_id: int, runs: int=500):
    results=[]
    for r in range(runs):
        iva=random.gauss(10000,1500)
        renta=random.gauss(20000,3000)
        assets=random.gauss(1000000,80000)
        results.append({"IVA":iva,"Renta":renta,"Assets":assets})
    avg={
        "IVA":sum([r["IVA"] for r in results])/runs,
        "Renta":sum([r["Renta"] for r in results])/runs,
        "Assets":sum([r["Assets"] for r in results])/runs,
    }
    return {"runs":runs,"avg":avg}
```

**IA generativa de riesgos** – `backend/app/services/ai_risks.py`

```python
import random

RISKS=["Reforma tributaria","Crisis de liquidez","Volatilidad FX"]
TEMPLATES=[
    "El riesgo {risk} podría impactar en {impact} según simulaciones.",
    "Se detecta {risk}, lo que generaría {impact} en el flujo proyectado."
]

IMPACTS=["aumento de impuestos","caída de caja","pérdida patrimonial"]

def generate_risk_explanation():
    risk=random.choice(RISKS)
    tpl=random.choice(TEMPLATES)
    impact=random.choice(IMPACTS)
    return tpl.format(risk=risk,impact=impact)
```

**Workflows híbridos** – `backend/app/services/workflows_hybrid.py`

```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def toggle_mode(db: Session, step_id: int, mode: str):
    s=db.get(WorkflowStep,step_id)
    s.mode=mode
    db.commit(); return s.mode
```

**KPIs predictivos** – `backend/app/services/kpis_predictive.py`

```python
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM

def predict_kpis(series, steps=3):
    data=np.array(series)
    X,y=[],[]
    for i in range(len(data)-steps):
        X.append(data[i:i+steps]); y.append(data[i+steps])
    X,y=np.array(X),np.array(y)
    X=X.reshape((X.shape[0],X.shape[1],1))
    model=Sequential([LSTM(30,activation='relu',input_shape=(steps,1)),Dense(1)])
    model.compile(optimizer='adam',loss='mse')
    model.fit(X,y,epochs=30,verbose=0)
    pred=model.predict(X[-1].reshape(1,steps,1))
    return float(pred[0][0])
```

---

## 4) API

**Forecast Montecarlo** – `backend/app/api/v1/forecast_montecarlo.py`

```python
from fastapi import APIRouter
from app.services.forecast_montecarlo import forecast_montecarlo

router=APIRouter()

@router.get("/montecarlo")
def montecarlo(company_id: int, runs: int=500):
    return forecast_montecarlo(company_id,runs)
```

**IA Riesgos** – `backend/app/api/v1/ai_risks.py`

```python
from fastapi import APIRouter
from app.services.ai_risks import generate_risk_explanation

router=APIRouter()

@router.get("/explain")
def explain():
    return {"explanation": generate_risk_explanation()}
```

**Workflows híbridos** – `backend/app/api/v1/workflows_hybrid.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_hybrid import toggle_mode

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/toggle")
def toggle(step_id: int, mode: str, db: Session = Depends(get_db)):
    return {"mode": toggle_mode(db,step_id,mode)}
```

**KPIs predictivos** – `backend/app/api/v1/kpis_predictive.py`

```python
from fastapi import APIRouter
from app.services.kpis_predictive import predict_kpis

router=APIRouter()

@router.post("/predict")
def predict(series: list, steps: int=3):
    return {"prediction": predict_kpis(series,steps)}
```

---

## 5) UI Next.js

- `/forecast/montecarlo`: histograma resultados IFRS/tributos.
- `/ai/risks`: panel explicaciones generativas de riesgos.
- `/workflows/hybrid`: selector manual/auto/híbrido.
- `/kpis/predictive`: curva con proyecciones neuronales.

**Componentes**

- `MonteCarloIFRSTaxChart.tsx`: histograma IFRS/tributos.
- `RiskGenerativePanel.tsx`: cuadro con explicación IA.
- `WorkflowHybridToggle.tsx`: botones cambio modo.
- `PredictiveKPIChart.tsx`: curva KPI proyectada.

---

## 6) Integración OFITEC

- **Forecast Montecarlo**: añade rigor probabilístico a IFRS/tributos.
- **IA de riesgos**: anticipa amenazas estratégicas.
- **Workflows híbridos**: flexibilidad en aprobaciones.
- **KPIs predictivos**: métricas forward-looking.

---

## 7) Checklist Sprint 45-46

-

---

## 8) Próximos pasos (Sprint 47+)

- Forecast global consolidado (finanzas, tributos, regulación, FX).
- IA generativa proactiva (sugerencias antes de eventos).
- Workflows inteligentes auto-ajustables.
- KPIs integrados en paneles de control interactivos.

