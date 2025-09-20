# OFITEC · Presupuestos/Mediciones – Sprint 29-30

Este Sprint apunta a la **consolidación global avanzada**: forecast multi-país/moneda, machine learning para predicción FX y BI interactivo embebido.

---

## 0) Objetivos
- **Forecast multi-país/moneda consolidado**: integrar FX dinámico en proyecciones.
- **ML para predicción FX**: entrenar modelo con históricos.
- **BI interactivo avanzado**: filtros y drill-down en dashboards embebidos.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0015_forecast_fx_bi.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0015_forecast_fx_bi"
down_revision = "0014_fx_reg_bi_alerts"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("fx_rates", sa.Column("source", sa.String()))
    op.add_column("fx_rates", sa.Column("predicted", sa.Boolean(), server_default="false"))

def downgrade():
    op.drop_column("fx_rates", "predicted")
    op.drop_column("fx_rates", "source")
```

---

## 2) Modelos
*(ya extendido en `fx_rates`)*

---

## 3) Servicios
**Forecast consolidado multi-país/moneda** – `backend/app/services/forecast_global.py`
```python
from sqlalchemy.orm import Session
from app.db.models.fx import FXRate
from app.db.models.invoice import Invoice
from app.db.models.company import Company

def forecast_multi(db: Session, years: int=3):
    companies = db.query(Company).all()
    result = {}
    for c in companies:
        invoices = db.query(Invoice).all()
        fx = db.query(FXRate).filter_by(currency="USD").order_by(FXRate.date.desc()).first()
        rate = float(fx.rate) if fx else 1
        result[c.name] = [{"year":2025+y,"net_usd": sum([float(i.amount or 0) for i in invoices])*rate} for y in range(years)]
    return result
```

**ML FX Prediction** – `backend/app/services/fx_ml.py`
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from app.db.models.fx import FXRate
from sqlalchemy.orm import Session

# Entrenamiento simple

def train_fx_model(db: Session, currency: str):
    rates = db.query(FXRate).filter_by(currency=currency).all()
    df = pd.DataFrame([{ "day": idx, "rate": float(r.rate) } for idx, r in enumerate(rates)])
    if len(df)<2: return None
    X,y = df[["day"]], df["rate"]
    model = LinearRegression().fit(X,y)
    return model

def predict_fx(db: Session, currency: str, days_ahead: int=30):
    model = train_fx_model(db, currency)
    if not model: return None
    last = len(db.query(FXRate).filter_by(currency=currency).all())
    pred = model.predict([[last+days_ahead]])[0]
    return round(float(pred),4)
```

**BI interactivo** – `backend/app/services/bi_interactive.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice

# Devuelve dataset enriquecido con filtros

def dataset_filtered(db: Session, status: str=None, min_amount: float=None):
    q = db.query(Invoice)
    if status: q=q.filter_by(status=status)
    if min_amount: q=q.filter(Invoice.amount>=min_amount)
    return [{"id":i.id,"amount":float(i.amount or 0),"status":i.status} for i in q.all()]
```

---

## 4) API
**Forecast consolidado** – `backend/app/api/v1/forecast_global.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.forecast_global import forecast_multi

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/multi")
def multi(years: int=3, db: Session = Depends(get_db)):
    return forecast_multi(db, years)
```

**FX ML** – `backend/app/api/v1/fx_ml.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.fx_ml import predict_fx

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/predict")
def predict(currency: str, days_ahead: int=30, db: Session = Depends(get_db)):
    return {"prediction": predict_fx(db, currency, days_ahead)}
```

**BI interactivo** – `backend/app/api/v1/bi_interactive.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_interactive import dataset_filtered

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/dataset")
def dataset(status: str=None, min_amount: float=None, db: Session = Depends(get_db)):
    return dataset_filtered(db, status, min_amount)
```

---

## 5) UI Next.js
- `/forecast/multi`: gráfico consolidado multi-país/moneda.
- `/fx/predict`: mostrar curva real vs proyectada.
- `/bi/interactive`: dashboard con filtros dinámicos.

**Componentes**
- `ForecastMultiChart.tsx`: gráfico stacked.
- `FXPredictChart.tsx`: línea comparando real vs predicción.
- `InteractiveBI.tsx`: tabla con filtros status/monto.

---

## 6) Integración OFITEC
- **Forecast multi-país/moneda** conecta IFRS forecast y tax scenarios.
- **FX ML** vía `ai_bridge` para entrenamiento más robusto.
- **BI interactivo** reemplaza export estático por exploración en vivo.

---

## 7) Checklist Sprint 29-30
- [ ] Migración 0015 aplicada.
- [ ] Forecast consolidado multi-país/moneda generado.
- [ ] Predicción ML FX entrenada y validada.
- [ ] BI interactivo embebido operativo.
- [ ] UI con gráficos y filtros desplegada.
- [ ] Tests Pytest de forecast, FX ML y BI.

---

## 8) Próximos pasos (Sprint 31+)
- Modelos ML avanzados (redes neuronales para FX).
- Forecast IFRS consolidado + sensibilidad tributaria.
- BI colaborativo (anotaciones, comentarios).
- Panel ejecutivo con recomendaciones automáticas IA.

