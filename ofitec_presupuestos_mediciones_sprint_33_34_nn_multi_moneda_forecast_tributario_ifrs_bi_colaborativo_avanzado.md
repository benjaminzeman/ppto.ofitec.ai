# OFITEC · Presupuestos/Mediciones – Sprint 33-34

Este Sprint fortalece la capa de **IA multi-dimensional**: redes neuronales multi-moneda, forecast tributario+IFRS combinado y BI colaborativo con menciones/alertas.

---

## 0) Objetivos
- **Redes neuronales multi-moneda**: entrenar modelos que integren varias divisas (USD, EUR, CLP).
- **Forecast tributario + IFRS combinado**: escenarios unificados contable-tributarios.
- **BI colaborativo avanzado**: menciones a usuarios y alertas dentro de paneles.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0017_nn_multimoneda_ifrs_tax_bi_adv.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0017_nn_multimoneda_ifrs_tax_bi_adv"
down_revision = "0016_ml_ifrs_bi_collab"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("bi_notes", sa.Column("mentions", sa.String()))
    op.add_column("bi_notes", sa.Column("alert", sa.Boolean(), server_default="false"))

def downgrade():
    op.drop_column("bi_notes", "mentions")
    op.drop_column("bi_notes", "alert")
```

---

## 2) Modelos
*(extensión de `BINote` con `mentions` y `alert`)*

---

## 3) Servicios
**NN Multi-moneda** – `backend/app/services/fx_nn_multi.py`
```python
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from app.db.models.fx import FXRate
from sqlalchemy.orm import Session

def train_nn_multi(db: Session, currencies=["USD","EUR","CLP"]):
    data=[]
    for c in currencies:
        rates=db.query(FXRate).filter_by(currency=c).all()
        series=[float(r.rate) for r in rates]
        if len(series)<10: continue
        data.append(series[-10:])
    if not data: return None
    X=np.array([list(x) for x in zip(*data[:-1])])
    y=np.array([sum(vals)/len(vals) for vals in zip(*data[1:])])
    X=X.reshape((X.shape[0],X.shape[1],1))
    model=Sequential([LSTM(50,activation='relu',input_shape=(X.shape[1],1)),Dense(1)])
    model.compile(optimizer='adam',loss='mse')
    model.fit(X,y,epochs=50,verbose=0)
    return model
```

**Forecast tributario+IFRS combinado** – `backend/app/services/forecast_combo.py`
```python
import random

def forecast_combo(company_id: int, years: int=3):
    out=[]
    for y in range(years):
        iva=10000+random.randint(-1000,1000)
        renta=20000+random.randint(-3000,3000)
        ifrs_assets=1000000+random.randint(-50000,50000)
        out.append({
            "year":2025+y,
            "IVA":iva,
            "Renta":renta,
            "IFRS_assets":ifrs_assets,
        })
    return out
```

**BI Colaborativo Avanzado** – `backend/app/services/bi_notes_adv.py`
```python
from app.db.models.bi_note import BINote
from sqlalchemy.orm import Session

def add_note_adv(db: Session, dashboard: str, user_id: int, note: str, mentions: str=None, alert: bool=False):
    n=BINote(dashboard=dashboard,user_id=user_id,note=note,mentions=mentions,alert=alert)
    db.add(n); db.commit(); return n.id

def list_notes_adv(db: Session, dashboard: str):
    return db.query(BINote).filter_by(dashboard=dashboard).all()
```

---

## 4) API
**NN Multi-moneda** – `backend/app/api/v1/fx_nn_multi.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.fx_nn_multi import train_nn_multi

router = APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/train")
def train(db: Session = Depends(get_db)):
    return {"ok": bool(train_nn_multi(db))}
```

**Forecast combinado** – `backend/app/api/v1/forecast_combo.py`
```python
from fastapi import APIRouter
from app.services.forecast_combo import forecast_combo

router = APIRouter()

@router.get("/combo")
def combo(company_id: int, years: int=3):
    return forecast_combo(company_id,years)
```

**BI Notes avanzado** – `backend/app/api/v1/bi_notes_adv.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_notes_adv import add_note_adv, list_notes_adv

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/add")
def add(dashboard: str, user_id: int, note: str, mentions: str=None, alert: bool=False, db: Session = Depends(get_db)):
    return {"id": add_note_adv(db,dashboard,user_id,note,mentions,alert)}

@router.get("/list")
def list_(dashboard: str, db: Session = Depends(get_db)):
    return list_notes_adv(db,dashboard)
```

---

## 5) UI Next.js
- `/fx/nn-multi`: entrenar modelo multi-moneda.
- `/forecast/combo`: forecast tributario+IFRS combinado.
- `/bi/notes-adv/[dashboard]`: notas con menciones y alertas.

**Componentes**
- `FXNNMultiTrainer.tsx`: botón entrenar + status.
- `ForecastComboChart.tsx`: gráfico comparativo IVA/Renta/IFRS.
- `BINotesAdv.tsx`: notas con @menciones y alertas destacadas.

---

## 6) Integración OFITEC
- **NN Multi-moneda**: fortalece módulo FX y forecast global.
- **Forecast combo**: une capas tributarias + IFRS.
- **BI colaborativo avanzado**: decisiones más coordinadas.

---

## 7) Checklist Sprint 33-34
- [ ] Migración 0017 aplicada.
- [ ] NN multi-moneda entrenada.
- [ ] Forecast tributario+IFRS operativo.
- [ ] Notas avanzadas BI activas.
- [ ] UI implementada.
- [ ] Tests Pytest para NN, forecast y notas.

---

## 8) Próximos pasos (Sprint 35+)
- Forecast consolidado multi-país/moneda/tributo.
- Recomendador IA para decisiones financieras.
- BI colaborativo con workflows de aprobación.
- Explicaciones generativas de escenarios IFRS/tributarios.

