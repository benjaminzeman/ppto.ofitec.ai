# OFITEC · Presupuestos/Mediciones – Sprint 67-68

Este Sprint apunta a la **auto-evolución del sistema**: forecast con auto-entrenamiento en tiempo real, narrativas colaborativas, workflows con reputación + feedback y KPIs estratégicos con simulación de objetivos.

---

## 0) Objetivos
- **Forecast auto-entrenado en tiempo real**: modelo que aprende y ajusta parámetros continuamente.
- **Narrativas colaborativas**: múltiples usuarios contribuyen a un mismo reporte.
- **Workflows reputación + feedback**: decisión ponderada con reputación y aprendizaje de retroalimentación.
- **KPIs estratégicos simulados**: comparar cumplimiento de objetivos estratégicos bajo distintos escenarios.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0034_forecast_autotrain_collab_narratives_reputation_feedback_kpis_simulation.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0034_forecast_autotrain_collab_narratives_reputation_feedback_kpis_simulation"
down_revision = "0033_forecast_ml_personalized_multimodal_workflows_reputation_kpis_strategic"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "collaborative_narratives",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content", sa.Text()),
        sa.Column("contributors", sa.JSON()),
    )

def downgrade():
    op.drop_table("collaborative_narratives")
```

---

## 2) Modelos
**`backend/app/db/models/collaborative_narrative.py`**
```python
from sqlalchemy import Column, Integer, Text, JSON
from app.db.base import Base

class CollaborativeNarrative(Base):
    __tablename__ = "collaborative_narratives"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    contributors = Column(JSON)
```

---

## 3) Servicios
**Forecast auto-entrenamiento** – `backend/app/services/forecast_autotrain.py`
```python
import random

HISTORY=[]

def forecast_autotrain(company_id: int, new_value: float):
    HISTORY.append(new_value)
    mean=sum(HISTORY)/len(HISTORY)
    forecast=random.gauss(mean,2000)
    return {"company_id":company_id,"forecast":forecast,"history_len":len(HISTORY)}
```

**Narrativas colaborativas** – `backend/app/services/ai_collab_narratives.py`
```python

def add_contribution(content: str, user: str, current: dict):
    current["contributors"].append(user)
    current["content"] += "\n"+content
    return current
```

**Workflows reputación + feedback** – `backend/app/services/workflows_rep_feedback.py`
```python
from app.db.models.role_reputation import RoleReputation
from sqlalchemy.orm import Session

def reputation_feedback_decision(db: Session, decisions: dict, feedback: dict):
    scores={r.role:r.score for r in db.query(RoleReputation).all()}
    weighted={}
    for role,dec in decisions.items():
        adj_score=scores.get(role,1)+feedback.get(role,0)
        weighted[dec]=weighted.get(dec,0)+adj_score
    return {"final":max(weighted,key=weighted.get),"weights":weighted}
```

**KPIs simulación estratégica** – `backend/app/services/kpis_simulation.py`
```python
import random

SCENARIOS=["Base","Optimista","Pesimista"]

def simulate_kpis(objectives: list):
    results={}
    for s in SCENARIOS:
        results[s]=[{"objective":o,"value":random.uniform(0.5,5.0)} for o in objectives]
    return results
```

---

## 4) API
**Forecast auto-entrenado** – `backend/app/api/v1/forecast_autotrain.py`
```python
from fastapi import APIRouter
from app.services.forecast_autotrain import forecast_autotrain

router=APIRouter()

@router.post("/autotrain")
def autotrain(company_id: int, new_value: float):
    return forecast_autotrain(company_id,new_value)
```

**Narrativas colaborativas** – `backend/app/api/v1/ai_collab_narratives.py`
```python
from fastapi import APIRouter
from app.services.ai_collab_narratives import add_contribution

router=APIRouter()

@router.post("/contribute")
def contribute(content: str, user: str, current: dict):
    return add_contribution(content,user,current)
```

**Workflows reputación+feedback** – `backend/app/api/v1/workflows_rep_feedback.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_rep_feedback import reputation_feedback_decision

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/decision")
def decision(decisions: dict, feedback: dict, db: Session = Depends(get_db)):
    return reputation_feedback_decision(db,decisions,feedback)
```

**KPIs simulación estratégica** – `backend/app/api/v1/kpis_simulation.py`
```python
from fastapi import APIRouter
from app.services.kpis_simulation import simulate_kpis

router=APIRouter()

@router.post("/simulate")
def simulate(objectives: list):
    return simulate_kpis(objectives)
```

---

## 5) UI Next.js
- `/forecast/autotrain`: forecast que aprende con cada input.
- `/ai/collab-narratives`: editor colaborativo.
- `/workflows/rep-feedback`: decisiones reputación + feedback.
- `/kpis/simulate`: simulación de KPIs estratégicos.

**Componentes**
- `AutotrainForecast.tsx`
- `CollaborativeNarratives.tsx`
- `ReputationFeedbackWorkflow.tsx`
- `SimulatedKPIs.tsx`

---

## 6) Integración OFITEC
- Forecast auto-entrenado continuo.
- Narrativas construidas en colaboración.
- Workflows reputación + feedback integrados.
- KPIs simulados para planeación estratégica.

---

## 7) Checklist Sprint 67-68
- [ ] Migración 0034 aplicada.
- [ ] Forecast auto-train operativo.
- [ ] Narrativas colaborativas activas.
- [ ] Workflows reputación+feedback funcionando.
- [ ] Simulación de KPIs estratégicos desplegada.
- [ ] UI integrada.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 69+)
- Forecast federado multi-empresa.
- Narrativas con IA generativa colaborativa.
- Workflows auto-adaptativos globales.
- KPIs estratégicos con benchmarking externo.

