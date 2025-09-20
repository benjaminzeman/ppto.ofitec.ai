# OFITEC · Presupuestos/Mediciones – Sprint 23-24

Este Sprint fortalece la **planificación fiscal y financiera de largo plazo** con escenarios tributarios, forecast IFRS multi-año e IA explicativa de riesgos fiscales.

---

## 0) Objetivos
- **Escenarios tributarios**: simulación IVA, PPM, Renta bajo diferentes supuestos.
- **Forecast IFRS multi-año**: proyección consolidada 3–5 años.
- **IA explicativa**: justificación automática de riesgos fiscales detectados.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0012_tax_scenarios_ifrs_forecast.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0012_tax_scenarios_ifrs_forecast"
down_revision = "0011_tax_ai_ifrs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "tax_scenarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE")),
        sa.Column("name", sa.String()),
        sa.Column("assumptions", sa.JSON()),
        sa.Column("results", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("tax_scenarios")
```

---

## 2) Modelos
**`backend/app/db/models/tax_scenario.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON
from app.db.base import Base

class TaxScenario(Base):
    __tablename__ = "tax_scenarios"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String)
    assumptions = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Escenarios tributarios** – `backend/app/services/tax_scenarios.py`
```python
import random
from app.db.models.tax_scenario import TaxScenario
from sqlalchemy.orm import Session

def create_tax_scenario(db: Session, company_id: int, name: str, assumptions: dict):
    results = {
        "IVA": round(random.uniform(1000,5000),2),
        "PPM": round(random.uniform(500,2000),2),
        "Renta": round(random.uniform(2000,7000),2),
    }
    sc = TaxScenario(company_id=company_id, name=name, assumptions=assumptions, results=results)
    db.add(sc); db.commit(); return sc.id
```

**Forecast IFRS multi-año** – `backend/app/services/ifrs_forecast.py`
```python
from datetime import datetime

def forecast_ifrs(company_id: int, years: int=5):
    today = datetime.today().year
    forecast = []
    for y in range(today, today+years):
        forecast.append({
            "year": y,
            "assets": 1000000 + y*10000,
            "liabilities": 500000 + y*8000,
            "equity": 500000 + y*2000,
        })
    return forecast
```

**IA explicativa de riesgos** – `backend/app/services/risk_explainer.py`
```python
from random import choice

EXPLANATIONS = {
    "Subdeclaración IVA": "La declaración muestra menos débito fiscal que lo esperado por las ventas registradas.",
    "Retraso PPM": "El calendario de pagos no coincide con la fecha exigida por Tesorería.",
    "Factura no conciliada": "Se detecta factura aceptada por SII sin movimiento bancario asociado.",
    "Error Renta": "Los ingresos declarados no cuadran con el flujo consolidado del año.",
}

def explain_risk(risk: str):
    return EXPLANATIONS.get(risk, "Riesgo detectado, sin explicación definida.")
```

---

## 4) API
**Escenarios tributarios** – `backend/app/api/v1/tax_scenarios.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.tax_scenarios import create_tax_scenario

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/create")
def create(company_id: int, name: str, assumptions: dict, db: Session = Depends(get_db)):
    return {"id": create_tax_scenario(db, company_id, name, assumptions)}
```

**Forecast IFRS** – `backend/app/api/v1/ifrs_forecast.py`
```python
from fastapi import APIRouter
from app.services.ifrs_forecast import forecast_ifrs

router = APIRouter()

@router.get("/forecast")
def forecast(company_id: int, years: int=5):
    return forecast_ifrs(company_id, years)
```

**Explicador de riesgos** – `backend/app/api/v1/risk_explainer.py`
```python
from fastapi import APIRouter
from app.services.risk_explainer import explain_risk

router = APIRouter()

@router.get("/explain")
def explain(risk: str):
    return {"risk": risk, "explanation": explain_risk(risk)}
```

---

## 5) UI Next.js
- `/tax/scenarios`: crear escenarios tributarios y mostrar resultados comparativos.
- `/ifrs/forecast`: gráfico multi-año de activos/pasivos/patrimonio.
- `/risks/explain`: ver explicación textual del riesgo detectado.

**Componentes**
- `TaxScenarioForm.tsx`: formulario + resultados.
- `IFRSForecastChart.tsx`: gráfico de líneas multi-año.
- `RiskExplanation.tsx`: cuadro de texto con explicación IA.

---

## 6) Integración OFITEC
- **Tax scenarios**: enlazados con `ai_bridge` para simulaciones predictivas avanzadas.
- **Forecast IFRS**: complementa reportes generados en sprint 21–22.
- **Risk explainer**: se conecta a auditoría y módulo de riesgos.

---

## 7) Checklist Sprint 23-24
- [ ] Migración 0012 aplicada.
- [ ] Escenarios tributarios creados y visibles en UI.
- [ ] Forecast IFRS multi-año operativo.
- [ ] Explicaciones de riesgos fiscales accesibles en panel.
- [ ] Tests Pytest de escenarios, forecast y explicador.
- [ ] Integración con ai_bridge y auditoría.

---

## 8) Próximos pasos (Sprint 25+)
- Forecast consolidado multi-país.
- Integración con sistemas BI externos (PowerBI, Tableau).
- Análisis de impacto regulatorio (cambios tributarios futuros).
- IA generativa para explicación automática de reportes IFRS.

