# OFITEC · Presupuestos/Mediciones – Sprint 47-48

Este Sprint busca cerrar el círculo con una **visión global unificada y proactiva**: forecast consolidado, IA anticipativa, workflows inteligentes auto-ajustables y KPIs interactivos en paneles ejecutivos.

---

## 0) Objetivos
- **Forecast global consolidado**: finanzas, tributos, regulación y FX en un único modelo.
- **IA proactiva**: sugerir acciones antes de eventos críticos.
- **Workflows inteligentes**: auto-ajustarse con base en contexto/riesgo.
- **KPIs interactivos**: panel dinámico con filtros y exploración visual.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0024_forecast_proactive_workflows_kpis_interactive.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0024_forecast_proactive_workflows_kpis_interactive"
down_revision = "0023_forecast_risks_workflows_kpis_pred"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "proactive_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer),
        sa.Column("message", sa.String()),
        sa.Column("severity", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("proactive_alerts")
```

---

## 2) Modelos
**`backend/app/db/models/proactive_alert.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base

class ProactiveAlert(Base):
    __tablename__ = "proactive_alerts"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer)
    message = Column(String)
    severity = Column(String)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Forecast global consolidado** – `backend/app/services/forecast_global_consolidated.py`
```python
import random

def forecast_global_consolidated(company_id: int, years: int=3):
    out=[]
    for y in range(years):
        iva=random.randint(9000,11000)
        renta=random.randint(18000,22000)
        fx=random.uniform(800,950)
        reg=random.choice(["Ley IVA","Reforma Renta","Norma IFRS"])
        out.append({"year":2025+y,"IVA":iva,"Renta":renta,"FX":fx,"Reg":reg})
    return out
```

**IA proactiva** – `backend/app/services/ai_proactive.py`
```python
import random

MESSAGES=[
    ("Liquidez baja proyectada en 30 días","alta"),
    ("Posible retraso en pago de clientes","media"),
    ("Nueva normativa tributaria detectada","alta")
]

def generate_proactive_alerts(company_id: int):
    msg,severity=random.choice(MESSAGES)
    return {"company_id":company_id,"message":msg,"severity":severity}
```

**Workflows inteligentes** – `backend/app/services/workflows_intelligent.py`
```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

# Auto-ajusta aprobaciones: si riesgo alto, añade paso extra.

def adjust_workflow(db: Session, note_id: int, risk_level: str):
    steps=db.query(WorkflowStep).filter_by(note_id=note_id).all()
    if risk_level=="alto":
        extra=WorkflowStep(note_id=note_id,role="Directorio",order=len(steps)+1,status="pending")
        db.add(extra); db.commit()
        return "step added"
    return "no change"
```

**KPIs interactivos** – `backend/app/services/kpis_interactive.py`
```python
import random

KPI_LIST=["Margen Neto","Ebitda","Cash Ratio","DSCR"]

def generate_kpis_interactive(filters: dict=None):
    return [{"kpi":k,"value":round(random.uniform(0.5,3.0),2)} for k in KPI_LIST]
```

---

## 4) API
**Forecast consolidado** – `backend/app/api/v1/forecast_global_consolidated.py`
```python
from fastapi import APIRouter
from app.services.forecast_global_consolidated import forecast_global_consolidated

router=APIRouter()

@router.get("/consolidated")
def consolidated(company_id: int, years: int=3):
    return forecast_global_consolidated(company_id,years)
```

**IA Proactiva** – `backend/app/api/v1/ai_proactive.py`
```python
from fastapi import APIRouter
from app.services.ai_proactive import generate_proactive_alerts

router=APIRouter()

@router.get("/alerts")
def alerts(company_id: int):
    return generate_proactive_alerts(company_id)
```

**Workflows inteligentes** – `backend/app/api/v1/workflows_intelligent.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflows_intelligent import adjust_workflow

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/adjust")
def adjust(note_id: int, risk_level: str, db: Session = Depends(get_db)):
    return {"result": adjust_workflow(db,note_id,risk_level)}
```

**KPIs interactivos** – `backend/app/api/v1/kpis_interactive.py`
```python
from fastapi import APIRouter
from app.services.kpis_interactive import generate_kpis_interactive

router=APIRouter()

@router.get("/interactive")
def interactive():
    return generate_kpis_interactive()
```

---

## 5) UI Next.js
- `/forecast/consolidated`: tabla IFRS/tributos/FX/regulación.
- `/ai/proactive`: panel con alertas proactivas.
- `/workflows/intelligent`: lista ajustada dinámicamente.
- `/kpis/interactive`: dashboard con filtros.

**Componentes**
- `ConsolidatedForecast.tsx`: tabla consolidada.
- `ProactiveAlerts.tsx`: tarjetas alertas.
- `IntelligentWorkflow.tsx`: lista ajustada.
- `InteractiveKPIs.tsx`: dashboard con filtros.

---

## 6) Integración OFITEC
- Forecast unificado global.
- IA anticipativa integrada a dashboards.
- Workflows sensibles a riesgo.
- KPIs interactivos para directorio.

---

## 7) Checklist Sprint 47-48
- [ ] Migración 0024 aplicada.
- [ ] Forecast consolidado operativo.
- [ ] IA proactiva en marcha.
- [ ] Workflows inteligentes funcionando.
- [ ] KPIs interactivos desplegados.
- [ ] UI completa integrada.
- [ ] Tests Pytest de forecast, IA, workflows y KPIs.

---

## 8) Próximos pasos (Sprint 49+)
- Forecast global con escenarios probabilísticos.
- IA generativa para decisiones proactivas.
- Workflows híbridos multi-empresa.
- KPIs en tiempo real con streaming de datos.

