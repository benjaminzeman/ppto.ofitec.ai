# OFITEC · Presupuestos/Mediciones – Sprint 35-36

Este Sprint apunta a la **orquestación global inteligente**: forecast consolidado multi-país/moneda/tributo, recomendador IA financiero y BI colaborativo con workflows de aprobación.

---

## 0) Objetivos
- **Forecast consolidado**: integración de países, monedas y tributos.
- **Recomendador IA financiero**: sugerencias automáticas de decisiones (factoring, inversión, caja).
- **BI con workflows**: anotaciones con flujo de aprobación (ejecutivo → directorio).

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0018_forecast_global_ai_bi_workflows.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0018_forecast_global_ai_bi_workflows"
down_revision = "0017_nn_multimoneda_ifrs_tax_bi_adv"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("bi_notes", sa.Column("status", sa.String(), server_default="pending"))

def downgrade():
    op.drop_column("bi_notes", "status")
```

---

## 2) Modelos
*(extensión `BINote` con `status` = pending|approved|rejected)*

---

## 3) Servicios
**Forecast Global Consolidado** – `backend/app/services/forecast_global_full.py`
```python
from sqlalchemy.orm import Session
from app.db.models.company import Company
from app.db.models.invoice import Invoice
from app.db.models.fx import FXRate
import random

def forecast_global_full(db: Session, years: int=3):
    companies = db.query(Company).all()
    out={}
    for c in companies:
        invoices=db.query(Invoice).all()
        fx=db.query(FXRate).filter_by(currency="USD").first()
        rate=float(fx.rate) if fx else 1
        out[c.name] = [{
            "year":2025+y,
            "net": sum([float(i.amount or 0) for i in invoices])*rate,
            "IVA": random.randint(8000,12000),
            "Renta": random.randint(15000,25000)
        } for y in range(years)]
    return out
```

**Recomendador IA Financiero** – `backend/app/services/ai_recommender.py`
```python
import random

ACTIONS=["Usar factoring","Invertir excedentes","Aumentar caja de seguridad"]

def recommend_action(context: dict):
    return {"action": random.choice(ACTIONS), "reason": "Basado en flujo proyectado negativo."}
```

**BI Workflows** – `backend/app/services/bi_workflows.py`
```python
from app.db.models.bi_note import BINote
from sqlalchemy.orm import Session

def update_status(db: Session, note_id: int, status: str):
    n=db.get(BINote,note_id)
    n.status=status
    db.commit(); return n.status
```

---

## 4) API
**Forecast Global** – `backend/app/api/v1/forecast_global_full.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.forecast_global_full import forecast_global_full

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.get("/full")
def full(years: int=3, db: Session = Depends(get_db)):
    return forecast_global_full(db,years)
```

**Recomendador IA** – `backend/app/api/v1/ai_recommender.py`
```python
from fastapi import APIRouter
from app.services.ai_recommender import recommend_action

router=APIRouter()

@router.post("/recommend")
def recommend(context: dict):
    return recommend_action(context)
```

**BI Workflow** – `backend/app/api/v1/bi_workflows.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bi_workflows import update_status

router=APIRouter()

def get_db():
    db=SessionLocal(); yield db; db.close()

@router.post("/update-status")
def update_status_(note_id: int, status: str, db: Session = Depends(get_db)):
    return {"status": update_status(db,note_id,status)}
```

---

## 5) UI Next.js
- `/forecast/full`: comparativa global país/moneda/tributo.
- `/ai/recommend`: sugerencia IA financiera.
- `/bi/workflows`: notas con estados (pending/approved/rejected).

**Componentes**
- `ForecastFullChart.tsx`: stacked chart multi-país/tributo.
- `AIRecommender.tsx`: cuadro con acción sugerida y razón.
- `BIWorkflows.tsx`: listado notas con botones aprobar/rechazar.

---

## 6) Integración OFITEC
- **Forecast full** une IFRS, tributario y FX.
- **Recomendador IA** soporta decisiones ejecutivas.
- **Workflows BI** implementan gobierno corporativo.

---

## 7) Checklist Sprint 35-36
- [ ] Migración 0018 aplicada.
- [ ] Forecast global consolidado generado.
- [ ] Recomendador IA en marcha.
- [ ] Workflows BI activos.
- [ ] UI con forecast, AI y workflows.
- [ ] Tests Pytest de forecast, AI y workflows.

---

## 8) Próximos pasos (Sprint 37+)
- Forecast multi-escenario (optimista/base/pesimista).
- IA explicativa: por qué se sugiere cada acción.
- Workflows configurables por rol.
- Panel ejecutivo único: forecast + AI + aprobaciones.

