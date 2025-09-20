# OFITEC · Presupuestos/Mediciones – Sprint 53-54

Este Sprint lleva a OFITEC hacia la **resiliencia estratégica y la explicación automática**: forecast resiliente multi-año, IA generativa de mitigación de riesgos, workflows auto-optimizados y KPIs narrativos.

---

## 0) Objetivos
- **Forecast resiliente multi-año**: simulaciones a 5–10 años con choques y resiliencia.
- **IA de mitigación de riesgos**: recomendaciones automáticas para reducir impactos.
- **Workflows auto-optimizados**: ajustar dinámicamente niveles, roles y tiempos.
- **KPIs narrativos**: explicaciones en lenguaje natural para directorios y reportes.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0027_resilient_forecast_ai_risks_workflows_kpis_narrative.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0027_resilient_forecast_ai_risks_workflows_kpis_narrative"
down_revision = "0026_stress_ai_reg_workflows_kpis_comp"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "narrative_kpis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kpi", sa.String()),
        sa.Column("narrative", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("narrative_kpis")
```

---

## 2) Modelos
**`backend/app/db/models/narrative_kpi.py`**
```python
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base

class NarrativeKPI(Base):
    __tablename__ = "narrative_kpis"
    id = Column(Integer, primary_key=True)
    kpi = Column(String)
    narrative = Column(Text)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Forecast resiliente multi-año** – `backend/app/services/forecast_resilient.py`
```python
import random

def forecast_resilient(company_id: int, years: int=10):
    out=[]
    for y in range(years):
        cash=random.gauss(50000,15000)
        stress=random.choice(["shock FX","caída demanda","alza impuestos"])
        resilience=cash+random.randint(5000,20000)
        out.append({"year":2025+y,"cash":cash,"stress":stress,"resilience":resilience})
    return out
```

**IA mitigación de riesgos** – `backend/app/services/ai_risk_mitigation.py`
```python
import random

MITIGATIONS=["Aumentar liquidez","Diversificar proveedores","Coberturas FX","Optimizar gastos"]

def suggest_mitigation():
    return {"mitigation":random.choice(MITIGATIONS)}
```

**Workflows auto-optimizados** – `backend/app/services/workflows_auto_opt.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def optimize_workflows(db: Session, company_id: int):
    steps=db.query(WorkflowStep).filter_by(status="pending").all()
    for s in steps:
        s.order=max(1,s.order-1) # acelera
    db.commit()
    return {"optimized":len(steps)}
```

**KPIs narrativos** – `backend/app/services/kpis_narrative.py`
```python
import random

NARRATIVES=["Margen neto en alza por eficiencia.","Liquidez en riesgo por FX.","DSCR estable con factoring."]

def generate_narratives():
    return [{"kpi":"Random","narrative":random.choice(NARRATIVES)}]
```

---

## 4) API
**Forecast resiliente** – `backend/app/api/v1/forecast_resilient.py`
```python
from fastapi import APIRouter
from app.services.forecast_resilient import forecast_resilient

router=APIRouter()

@router.get("/resilient")
def resilient(company_id: int, years: int=10):
    return forecast_resilient(company_id,years)
```

**IA mitigación** – `backend/app/api/v1/ai_risk_mitigation.py`
```python
from fastapi import APIRouter
from app.services.ai_risk_mitigation import suggest_mitigation

router=APIRouter()

@router.get("/mitigation")
def mitigation():
    return suggest_mitigation()
```

**Workflows auto-optimizados** – `backend/app/api/v1/workflows_auto_opt.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_auto_opt import optimize_workflows

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/optimize")
def optimize(company_id: int, db: Session = Depends(get_db)):
    return optimize_workflows(db,company_id)
```

**KPIs narrativos** – `backend/app/api/v1/kpis_narrative.py`
```python
from fastapi import APIRouter
from app.services.kpis_narrative import generate_narratives

router=APIRouter()

@router.get("/narratives")
def narratives():
    return generate_narratives()
```

---

## 5) UI Next.js
- `/forecast/resilient`: gráfico multi-año + choques.
- `/ai/mitigation`: tarjetas con sugerencias.
- `/workflows/optimize`: vista con pasos acelerados.
- `/kpis/narratives`: dashboard con texto explicativo.

**Componentes**
- `ResilientForecastChart.tsx`
- `RiskMitigationCards.tsx`
- `OptimizedWorkflows.tsx`
- `NarrativeKPIs.tsx`

---

## 6) Integración OFITEC
- Forecast resiliente unido a stress tests.
- IA de mitigación como recomendador preventivo.
- Workflows auto-optimizados para agilidad.
- Narrativas integradas en reportes ejecutivos.

---

## 7) Checklist Sprint 53-54
- [ ] Migración 0027 aplicada.
- [ ] Forecast resiliente implementado.
- [ ] IA mitigación activa.
- [ ] Workflows auto-optimizados funcionando.
- [ ] KPIs narrativos generados.
- [ ] UI integrada.
- [ ] Tests completos.

---

## 8) Próximos pasos (Sprint 55+)
- Forecast resiliente con sensibilidad multi-escenario.
- IA explicativa narrativa larga.
- Workflows globales auto-aprendizaje.
- KPIs integrados con storytelling visual.

