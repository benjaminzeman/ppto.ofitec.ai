# OFITEC · Presupuestos/Mediciones – Sprint 65-66

Este Sprint combina **machine learning continuo y personalización estratégica**: forecast auto-sintonizado con ML, narrativas multimodales personalizadas, workflows con IA reputacional y KPIs ligados a objetivos estratégicos.

---

## 0) Objetivos
- **Forecast ML continuo**: modelo entrenado con datos históricos que se reentrena periódicamente.
- **Narrativas multimodales personalizadas**: reportes que mezclan texto, visuales y recomendaciones según perfil.
- **Workflows IA reputacional**: decisiones ponderadas con modelos de reputación entrenados.
- **KPIs estratégicos**: métricas alineadas a objetivos estratégicos de la empresa.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0033_forecast_ml_personalized_multimodal_workflows_reputation_kpis_strategic.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0033_forecast_ml_personalized_multimodal_workflows_reputation_kpis_strategic"
down_revision = "0032_autotune_forecast_personalized_narratives_reputation_kpis_rewards"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "strategic_kpis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("objective", sa.String()),
        sa.Column("kpi", sa.String()),
        sa.Column("value", sa.Float()),
    )

def downgrade():
    op.drop_table("strategic_kpis")
```

---

## 2) Modelos
**`backend/app/db/models/strategic_kpi.py`**
```python
from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class StrategicKPI(Base):
    __tablename__ = "strategic_kpis"
    id = Column(Integer, primary_key=True)
    objective = Column(String)
    kpi = Column(String)
    value = Column(Float)
```

---

## 3) Servicios
**Forecast ML continuo** – `backend/app/services/forecast_ml.py`
```python
import random

# mock simple: usa histórico para ajustar media

def forecast_ml(company_id: int, history: list):
    if history:
        mean=sum(history)/len(history)
    else:
        mean=50000
    forecast=random.gauss(mean,5000)
    return {"company_id":company_id,"forecast":forecast,"trained_on":len(history)}
```

**Narrativas multimodales personalizadas** – `backend/app/services/ai_multimodal_personalized.py`
```python

def multimodal_personalized(role: str):
    if role=="CFO":
        return {"narrative":"Liquidez y riesgo tributario.","visual":"tabla comparativa"}
    elif role=="CEO":
        return {"narrative":"Crecimiento y expansión global.","visual":"mapa estratégico"}
    else:
        return {"narrative":"Ejecución operativa.","visual":"gráfico de barras"}
```

**Workflows IA reputacional** – `backend/app/services/workflows_ai_reputation.py`
```python
from app.db.models.role_reputation import RoleReputation
from sqlalchemy.orm import Session

def ai_weighted_decision(db: Session, decisions: dict):
    scores={r.role:r.score for r in db.query(RoleReputation).all()}
    weighted={}
    for role,dec in decisions.items():
        weighted[dec]=weighted.get(dec,0)+scores.get(role,1)
    return {"final":max(weighted,key=weighted.get),"weights":weighted}
```

**KPIs estratégicos** – `backend/app/services/kpis_strategic.py`
```python
import random

OBJECTIVES=["Crecimiento","Liquidez","Eficiencia"]

def strategic_kpis():
    return [{"objective":o,"kpi":f"KPI-{i}","value":random.uniform(0.5,5.0)} for i,o in enumerate(OBJECTIVES)]
```

---

## 4) API
**Forecast ML** – `backend/app/api/v1/forecast_ml.py`
```python
from fastapi import APIRouter
from app.services.forecast_ml import forecast_ml

router=APIRouter()

@router.post("/ml")
def ml(company_id: int, history: list):
    return forecast_ml(company_id,history)
```

**Narrativas multimodales personalizadas** – `backend/app/api/v1/ai_multimodal_personalized.py`
```python
from fastapi import APIRouter
from app.services.ai_multimodal_personalized import multimodal_personalized

router=APIRouter()

@router.get("/multimodal-personalized")
def personalized(role: str):
    return multimodal_personalized(role)
```

**Workflows IA reputacional** – `backend/app/api/v1/workflows_ai_reputation.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_ai_reputation import ai_weighted_decision

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/ai-decision")
def ai_decision(decisions: dict, db: Session = Depends(get_db)):
    return ai_weighted_decision(db,decisions)
```

**KPIs estratégicos** – `backend/app/api/v1/kpis_strategic.py`
```python
from fastapi import APIRouter
from app.services.kpis_strategic import strategic_kpis

router=APIRouter()

@router.get("/strategic")
def strategic():
    return strategic_kpis()
```

---

## 5) UI Next.js
- `/forecast/ml`: panel con forecast ML.
- `/ai/multimodal-personalized`: narrativas personalizadas.
- `/workflows/ai-reputation`: decisiones IA reputacional.
- `/kpis/strategic`: KPIs estratégicos.

**Componentes**
- `MLForecastPanel.tsx`
- `PersonalizedMultimodal.tsx`
- `AIReputationWorkflow.tsx`
- `StrategicKPIs.tsx`

---

## 6) Integración OFITEC
- Forecast ML entrenado periódicamente.
- Narrativas multimodales adaptadas a rol.
- Workflows con reputación IA.
- KPIs alineados a estrategia.

---

## 7) Checklist Sprint 65-66
- [ ] Migración 0033 aplicada.
- [ ] Forecast ML operativo.
- [ ] Narrativas multimodales personalizadas activas.
- [ ] Workflows reputacionales IA listos.
- [ ] KPIs estratégicos en UI.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 67+)
- Forecast ML con auto-entrenamiento en tiempo real.
- Narrativas multimodales colaborativas.
- Workflows reputación + feedback IA.
- KPIs estratégicos con simulación de objetivos.

