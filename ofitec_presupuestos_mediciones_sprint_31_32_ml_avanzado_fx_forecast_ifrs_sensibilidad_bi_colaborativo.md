# OFITEC · Presupuestos/Mediciones – Sprint 31-32

Este Sprint lleva OFITEC a un nivel de **IA avanzada y colaboración ejecutiva**: redes neuronales para FX, forecast IFRS con sensibilidad tributaria y BI colaborativo.

---

## 0) Objetivos
- **ML avanzado FX**: predicción con redes neuronales (LSTM).
- **Forecast IFRS + sensibilidad tributaria**: escenarios con variación IVA/PPM/Renta.
- **BI colaborativo**: anotaciones y comentarios en dashboards.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0016_ml_ifrs_bi_collab.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0016_ml_ifrs_bi_collab"
down_revision = "0015_forecast_fx_bi"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "bi_notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dashboard", sa.String()),
        sa.Column("user_id", sa.Integer),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("bi_notes")
```

---

## 2) Modelos
**`backend/app/db/models/bi_note.py`**
```python
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base

class BINote(Base):
    __tablename__ = "bi_notes"
    id = Column(Integer, primary_key=True)
    dashboard = Column(String)
    user_id = Column(Integer)
    note = Column(Text)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**ML Avanzado FX** – `backend/app/services/fx_nn.py`
```python
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from app.db.models.fx import FXRate
from sqlalchemy.orm import Session

def train_nn_fx(db: Session, currency: str):
    rates = db.query(FXRate).filter_by(currency=currency).all()
    data = np.array([float(r.rate) for r in rates])
    if len(data)<10: return None
    X,y=[],[]
    for i in range(len(data)-3):
        X.append(data[i:i+3]); y.append(data[i+3])
    X,y=np.array(X),np.array(y)
    X=X.reshape((X.shape[0],X.shape[1],1))
    model=Sequential([LSTM(50,activation='relu',input_shape=(3,1)),Dense(1)])
    model.compile(optimizer='adam',loss='mse')
    model.fit(X,y,epochs=50,verbose=0)
    return model
```

**Forecast IFRS con sensibilidad** – `backend/app/services/ifrs_sensitivity.py`
```python
import random

def forecast_ifrs_sensitivity(company_id: int, tax_variation: dict, years: int=3):
    out=[]
    for y in range(years):
        iva = 10000*(1+tax_variation.get("IVA",0.1))
        ppm = 5000*(1+tax_variation.get("PPM",0.05))
        renta = 20000*(1+tax_variation.get("Renta",0.2))
        out.append({"year":2025+y,"IVA":iva,"PPM":ppm,"Renta":renta})
    return out
```

**BI Colaborativo** – `backend/app/services/bi_notes.py`
```python
from app.db.models.bi_note import BINote
from sqlalchemy.orm import Session

def add_note(db: Session, dashboard: str, user_id: int, note: str):
    n = BINote(dashboard=dashboard, user_id=user_id, note=note)
    db.add(n); db.commit(); return n.id

def list_notes(db: Session, dashboard: str):
    return db.query(BINote).filter_by(dashboard=dashboard).all()
```

---

## 4) API
**FX NN** – `backend/app/api/v1/fx_nn.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.fx_nn import train_nn_fx

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/train")
def train(currency: str, db: Session = Depends(get_db)):
    return {"ok": bool(train_nn_fx(db,currency))}
```

**IFRS Sensitivity** – `backend/app/api/v1/ifrs_sensitivity.py`
```python
from fastapi import APIRouter
from app.services.ifrs_sensitivity import forecast_ifrs_sensitivity

router = APIRouter()

@router.post("/forecast")
def forecast(company_id: int, tax_variation: dict, years: int=3):
    return forecast_ifrs_sensitivity(company_id, tax_variation, years)
```

**BI Notes** – `backend/app/api/v1/bi_notes.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_notes import add_note, list_notes

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/add")
def add(dashboard: str, user_id: int, note: str, db: Session = Depends(get_db)):
    return {"id": add_note(db,dashboard,user_id,note)}

@router.get("/list")
def list_(dashboard: str, db: Session = Depends(get_db)):
    return list_notes(db,dashboard)
```

---

## 5) UI Next.js
- `/fx/nn-train`: botón entrenar modelo NN.
- `/ifrs/sensitivity`: formulario variación tributaria + forecast.
- `/bi/notes/[dashboard]`: notas colaborativas en cada panel.

**Componentes**
- `FXNNTrainer.tsx`: botón entrenar + status.
- `IFRSSensitivityChart.tsx`: líneas comparativas con variaciones.
- `BINotes.tsx`: listado y formulario de notas.

---

## 6) Integración OFITEC
- **FX NN**: mejora predicciones de módulo FX.
- **IFRS Sensibilidad**: complementa escenarios tributarios.
- **BI Colaborativo**: fomenta decisiones compartidas.

---

## 7) Checklist Sprint 31-32
- [ ] Migración 0016 aplicada.
- [ ] NN FX entrenada y probada.
- [ ] Forecast IFRS sensibilidad operativo.
- [ ] Notas BI colaborativas activas.
- [ ] UI con entrenar, forecast y notas.
- [ ] Tests Pytest de NN FX, IFRS sens y notas.

---

## 8) Próximos pasos (Sprint 33+)
- Redes neuronales recurrentes multi-moneda.
- Forecast tributario + IFRS combinado.
- BI colaborativo con menciones y alertas.
- IA generativa para explicar escenarios contables complejos.

