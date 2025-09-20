# OFITEC · Presupuestos/Mediciones – Sprint 25-26

Este Sprint expande la visión a nivel internacional: **forecast multi-país**, **integración con BI externo** y **análisis regulatorio futuro**.

---

## 0) Objetivos
- **Forecast consolidado multi-país**: proyecciones financieras y tributarias por país.
- **Integración BI externo**: exponer datasets a PowerBI/Tableau.
- **Análisis regulatorio**: anticipar impacto de cambios tributarios.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0013_multipais_bi_regulacion.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0013_multipais_bi_regulacion"
down_revision = "0012_tax_scenarios_ifrs_forecast"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("companies", sa.Column("country", sa.String()))
    op.create_table(
        "regulatory_changes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("country", sa.String()),
        sa.Column("law_name", sa.String()),
        sa.Column("impact", sa.Text()),
        sa.Column("effective_date", sa.Date()),
    )

def downgrade():
    op.drop_table("regulatory_changes")
    op.drop_column("companies", "country")
```

---

## 2) Modelos
**`backend/app/db/models/regulatory.py`**
```python
from sqlalchemy import Column, Integer, String, Date
from app.db.base import Base

class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"
    id = Column(Integer, primary_key=True)
    country = Column(String)
    law_name = Column(String)
    impact = Column(String)
    effective_date = Column(Date)
```

---

## 3) Servicios
**Forecast multi-país** – `backend/app/services/multipais.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice
from app.db.models.company import Company

def forecast_global(db: Session, years: int=3):
    companies = db.query(Company).all()
    forecast = {}
    for c in companies:
        invoices = db.query(Invoice).all()
        total = sum([float(i.amount or 0) for i in invoices])
        forecast[c.country] = [{"year":2025+y,"net": total*0.1*(y+1)} for y in range(years)]
    return forecast
```

**Integración BI** – `backend/app/services/bi_export.py`
```python
import pandas as pd
from app.db.models.invoice import Invoice

def export_dataset(db, path: str):
    invoices = db.query(Invoice).all()
    df = pd.DataFrame([{ "id":i.id, "amount": float(i.amount or 0), "status": i.status } for i in invoices])
    df.to_csv(path,index=False); return path
```

**Regulación** – `backend/app/services/regulation.py`
```python
from app.db.models.regulatory import RegulatoryChange
from sqlalchemy.orm import Session

def list_regulations(db: Session, country: str):
    return db.query(RegulatoryChange).filter_by(country=country).all()
```

---

## 4) API
**Forecast multi-país** – `backend/app/api/v1/multipais.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.multipais import forecast_global

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/forecast")
def forecast(years: int=3, db: Session = Depends(get_db)):
    return forecast_global(db, years)
```

**BI Export** – `backend/app/api/v1/bi.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_export import export_dataset
import tempfile

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/export")
def export(db: Session = Depends(get_db)):
    path = tempfile.mktemp(suffix=".csv")
    return {"file": export_dataset(db, path)}
```

**Regulación** – `backend/app/api/v1/regulation.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.regulation import list_regulations

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/{country}")
def regulations(country: str, db: Session = Depends(get_db)):
    return list_regulations(db, country)
```

---

## 5) UI Next.js
- `/forecast/global`: gráfico comparativo multi-país.
- `/bi/export`: botón exportar dataset a CSV.
- `/regulation/[country]`: lista de cambios regulatorios futuros.

**Componentes**
- `GlobalForecastChart.tsx`: gráfico stacked por país.
- `BIExportButton.tsx`: botón descarga CSV.
- `RegulationList.tsx`: tabla de leyes y fechas.

---

## 6) Integración OFITEC
- **Forecast multi-país**: enlazado con IFRS forecast y tax scenarios.
- **BI Export**: datasets para PowerBI/Tableau en tiempo real.
- **Regulación**: módulo de riesgos actualizado con impacto normativo.

---

## 7) Checklist Sprint 25-26
- [ ] Migración 0013 aplicada.
- [ ] Forecast multi-país generado.
- [ ] Export dataset BI disponible.
- [ ] Cambios regulatorios listados.
- [ ] UI con forecast, export y regulación.
- [ ] Tests Pytest de forecast, export y regulation.

---

## 8) Próximos pasos (Sprint 27+)
- Forecast multi-moneda (FX dinámico).
- Integración con feeds regulatorios oficiales.
- BI embebido dentro de OFITEC.
- Panel de alertas globales (país/moneda/regulación).

