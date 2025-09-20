# OFITEC · Presupuestos/Mediciones – Sprint 39-40

Este Sprint lleva OFITEC a un nivel de **planeación estratégica integral**: forecast multi-escenario IFRS+tributos, IA con simulaciones, workflows multinivel y panel con KPIs dinámicos.

---

## 0) Objetivos

- **Forecast combinado IFRS+tributos**: escenarios integrados financieros y fiscales.
- **IA simuladora**: probar distintas acciones y visualizar resultados.
- **Workflows multinivel**: varios aprobadores en secuencia.
- **KPIs dinámicos**: panel ejecutivo con indicadores ajustables.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0020_ifrs_tax_ai_workflows_kpis"
down_revision = "0019_multi_scenarios_ai_roles_panel"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("bi_notes.id", ondelete="CASCADE")),
        sa.Column("role", sa.String()),
        sa.Column("order", sa.Integer),
        sa.Column("status", sa.String(), server_default="pending"),
    )

def downgrade():
    op.drop_table("workflow_steps")
```

---

## 2) Modelos

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String
from app.db.base import Base

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("bi_notes.id", ondelete="CASCADE"))
    role = Column(String)
    order = Column(Integer)
    status = Column(String, default="pending")
```

---

## 3) Servicios

**Forecast IFRS+tributos** – `backend/app/services/forecast_ifrs_tax.py`

```python
import random

def forecast_ifrs_tax(company_id: int, years: int=3):
    out=[]
    for y in range(years):
        iva = random.randint(8000,12000)
        renta = random.randint(15000,25000)
        assets = random.randint(900000,1100000)
        out.append({"year":2025+y,"IVA":iva,"Renta":renta,"Assets":assets})
    return out
```

**IA simuladora** – `backend/app/services/ai_simulator.py`

```python
ACTIONS=["Usar factoring","Invertir excedentes","Aumentar caja de seguridad"]


def simulate_action(action: str):
    if action=="Usar factoring":
        return {"impact":"+20% liquidez inmediata","risk":"Costo financiero adicional"}
    if action=="Invertir excedentes":
        return {"impact":"+10% retorno esperado","risk":"Exposición a mercado"}
    if action=="Aumentar caja de seguridad":
        return {"impact":"Mayor resiliencia","risk":"Menor rendimiento capital"}
    return {"impact":"N/A","risk":"N/A"}
```

**Workflows multinivel** – `backend/app/services/workflow_steps.py`

```python
from app.db.models.workflow_step import WorkflowStep
from sqlalchemy.orm import Session

def add_step(db: Session, note_id: int, role: str, order: int):
    s=WorkflowStep(note_id=note_id,role=role,order=order)
    db.add(s); db.commit(); return s.id

def update_step(db: Session, step_id: int, status: str):
    s=db.get(WorkflowStep,step_id)
    s.status=status
    db.commit(); return s.status
```

**KPIs dinámicos** – `backend/app/services/kpis.py`

```python
import random

KPI_LIST=["Margen Neto","Ebitda","Deuda/EBITDA","Cash Ratio"]

def generate_kpis():
    return [{"kpi":k,"value":round(random.uniform(0.5,3.0),2)} for k in KPI_LIST]
```

---

## 4) API

**Forecast IFRS+Tax** – `backend/app/api/v1/forecast_ifrs_tax.py`

```python
from fastapi import APIRouter
from app.services.forecast_ifrs_tax import forecast_ifrs_tax

router=APIRouter()

@router.get("/ifrs-tax")
def ifrs_tax(company_id: int, years: int=3):
    return forecast_ifrs_tax(company_id,years)
```

**IA Simuladora** – `backend/app/api/v1/ai_simulator.py`

```python
from fastapi import APIRouter
from app.services.ai_simulator import simulate_action

router=APIRouter()

@router.get("/simulate")
def simulate(action: str):
    return simulate_action(action)
```

**Workflows Steps** – `backend/app/api/v1/workflow_steps.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.workflow_steps import add_step,update_step

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/add")
def add(note_id: int, role: str, order: int, db: Session = Depends(get_db)):
    return {"id": add_step(db,note_id,role,order)}

@router.post("/update")
def update(step_id: int, status: str, db: Session = Depends(get_db)):
    return {"status": update_step(db,step_id,status)}
```

**KPIs dinámicos** – `backend/app/api/v1/kpis.py`

```python
from fastapi import APIRouter
from app.services.kpis import generate_kpis

router=APIRouter()

@router.get("/generate")
def generate():
    return generate_kpis()
```

---

## 5) UI Next.js

- `/forecast/ifrs-tax`: tabla combinada IFRS+tributos.
- `/ai/simulator`: panel con impacto/riesgo de acciones.
- `/workflows/steps`: lista multinivel de aprobadores.
- `/executive/kpis`: KPIs dinámicos con filtros.

**Componentes**

- `IFRSTaxForecast.tsx`: tabla de forecast.
- `AISimulator.tsx`: cuadro acción-impacto-riesgo.
- `WorkflowSteps.tsx`: lista pasos con estado.
- `KPIsDynamic.tsx`: tarjetas con valores KPI.

---

## 6) Integración OFITEC

- **Forecast IFRS+tributos**: une visión fiscal y contable.
- **Simulador IA**: apoya decisiones ejecutivas.
- **Workflows multinivel**: jerarquía corporativa avanzada.
- **KPIs dinámicos**: panel vivo para directorio.

---

## 7) Checklist Sprint 39-40

-

---

## 8) Próximos pasos (Sprint 41+)

- Forecast integrado IFRS/tributos/regulación.
- IA generativa para recomendaciones explicativas.
- Workflows adaptativos (condiciones dinámicas).
- KPIs personalizados por usuario/rol.

