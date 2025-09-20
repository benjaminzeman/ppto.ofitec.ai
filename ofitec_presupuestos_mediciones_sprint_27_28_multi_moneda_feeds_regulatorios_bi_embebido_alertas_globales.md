# OFITEC · Presupuestos/Mediciones – Sprint 27-28

Este Sprint eleva OFITEC a un nivel **global**: gestión multi-moneda, conexión con feeds regulatorios, BI embebido y panel de alertas globales.

---

## 0) Objetivos
- **Multi-moneda (FX)**: forecast y reportes considerando tipo de cambio dinámico.
- **Feeds regulatorios oficiales**: ingestión automática de cambios tributarios.
- **BI embebido**: visualizaciones dentro de OFITEC (sin salir a PowerBI/Tableau).
- **Alertas globales**: panel consolidado por país, moneda y regulación.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0014_fx_reg_bi_alerts.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0014_fx_reg_bi_alerts"
down_revision = "0013_multipais_bi_regulacion"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("currency", sa.String()),
        sa.Column("rate", sa.Numeric(12,4)),
        sa.Column("date", sa.Date()),
    )
    op.create_table(
        "global_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("country", sa.String()),
        sa.Column("type", sa.String()),  # fx|regulation|risk
        sa.Column("message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("global_alerts")
    op.drop_table("fx_rates")
```

---

## 2) Modelos
**`backend/app/db/models/fx.py`**
```python
from sqlalchemy import Column, Integer, String, Date, Numeric
from app.db.base import Base

class FXRate(Base):
    __tablename__ = "fx_rates"
    id = Column(Integer, primary_key=True)
    currency = Column(String)
    rate = Column(Numeric(12,4))
    date = Column(Date)
```

**`backend/app/db/models/alert.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base import Base

class GlobalAlert(Base):
    __tablename__ = "global_alerts"
    id = Column(Integer, primary_key=True)
    country = Column(String)
    type = Column(String)
    message = Column(Text)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Multi-moneda** – `backend/app/services/fx.py`
```python
import requests, os
from app.db.models.fx import FXRate
from sqlalchemy.orm import Session

FX_API = os.getenv("FX_API")

def update_fx(db: Session, currency: str):
    r = requests.get(f"{FX_API}?base={currency}&symbols=USD")
    rate = r.json().get("rates",{}).get("USD",1)
    fx = FXRate(currency=currency, rate=rate)
    db.add(fx); db.commit(); return rate

def convert(amount: float, rate: float):
    return round(amount*rate,2)
```

**Feeds regulatorios** – `backend/app/services/reg_feeds.py`
```python
import requests

def fetch_regulations(country: str):
    url = f"https://api.regulatorios/{country}/changes"
    return requests.get(url).json()
```

**BI embebido** – `backend/app/services/bi_embed.py`
```python
# Simulación: exportar dataset en JSON listo para gráficos internos
from app.db.models.invoice import Invoice
from sqlalchemy.orm import Session

def dataset_json(db: Session):
    invoices = db.query(Invoice).all()
    return [{"id":i.id,"amount":float(i.amount or 0),"status":i.status} for i in invoices]
```

**Alertas globales** – `backend/app/services/alerts_global.py`
```python
from app.db.models.alert import GlobalAlert
from sqlalchemy.orm import Session

def create_alert(db: Session, country: str, type_: str, message: str):
    a = GlobalAlert(country=country,type=type_,message=message)
    db.add(a); db.commit(); return a.id

def list_alerts(db: Session, country: str=None):
    q = db.query(GlobalAlert)
    if country: q=q.filter_by(country=country)
    return q.all()
```

---

## 4) API
**FX** – `backend/app/api/v1/fx.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.fx import update_fx, convert

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/update")
def update(currency: str, db: Session = Depends(get_db)):
    return {"rate": update_fx(db, currency)}

@router.get("/convert")
def convert_(amount: float, rate: float):
    return {"converted": convert(amount, rate)}
```

**Regulatorios** – `backend/app/api/v1/reg_feeds.py`
```python
from fastapi import APIRouter
from app.services.reg_feeds import fetch_regulations

router = APIRouter()

@router.get("/{country}")
def fetch(country: str):
    return fetch_regulations(country)
```

**BI embebido** – `backend/app/api/v1/bi_embed.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_embed import dataset_json

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/dataset")
def dataset(db: Session = Depends(get_db)):
    return dataset_json(db)
```

**Alertas globales** – `backend/app/api/v1/alerts_global.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.alerts_global import create_alert, list_alerts

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/create")
def create(country: str, type_: str, message: str, db: Session = Depends(get_db)):
    return {"id": create_alert(db, country, type_, message)}

@router.get("/list")
def list_(country: str=None, db: Session = Depends(get_db)):
    return list_alerts(db, country)
```

---

## 5) UI Next.js
- `/fx`: actualizar tasas y convertir.
- `/regulations/feeds`: vista automática de cambios regulatorios.
- `/bi/embed`: dashboards internos (charts, tablas).
- `/alerts/global`: panel de alertas globales.

**Componentes**
- `FXUpdater.tsx`: formulario actualización tasas.
- `RegFeedView.tsx`: lista de cambios regulatorios.
- `EmbeddedBI.tsx`: gráficos internos (bar/line).
- `GlobalAlertsPanel.tsx`: tarjetas con alertas filtradas.

---

## 6) Integración OFITEC
- **FX** enlazado con forecast IFRS y escenarios tributarios.
- **Feeds regulatorios** conectados al módulo de riesgos.
- **BI embebido** complementa export PowerBI/Tableau.
- **Alertas globales** integran datos de riesgos, FX y regulación.

---

## 7) Checklist Sprint 27-28
- [ ] Migración 0014 aplicada.
- [ ] FX rates actualizados y aplicados en forecasts.
- [ ] Feeds regulatorios consumidos.
- [ ] Dataset embebido disponible.
- [ ] Panel de alertas funcionando.
- [ ] Tests Pytest de FX, feeds, BI y alertas.
- [ ] Auditoría de alertas registrada.

---

## 8) Próximos pasos (Sprint 29+)
- Forecast multi-país multi-moneda consolidado.
- Machine learning para predicción FX.
- Regulación proactiva: alertas antes de vigencia legal.
- BI interactivo avanzado (filtros, drill-downs).

