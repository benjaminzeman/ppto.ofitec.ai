# OFITEC · Presupuestos/Mediciones – Sprint 19-20

En este Sprint incorporamos **IA contable**, **comparativas multi-empresa históricas** y **cumplimiento tributario (SII/Tesorería)**. Esto asegura trazabilidad fiscal y análisis estratégico avanzado.

---

## 0) Objetivos
- **IA contable**: clasificación automática de gastos/ingresos con ML/ai_bridge.
- **Comparativas multi-empresa históricas**: evolución de KPIs entre empresas y periodos.
- **Cumplimiento tributario**: conexión con SII y Tesorería (validación IVA, pagos de impuestos).
- **Auditoría extendida**: trazabilidad completa de cada asiento contable.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0010_ai_multi_tax.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0010_ai_multi_tax"
down_revision = "0009_accounting_signing_multi"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("date", sa.Date()),
        sa.Column("description", sa.String()),
        sa.Column("amount", sa.Numeric(16,2)),
        sa.Column("category", sa.String()),
        sa.Column("classified_by_ai", sa.Boolean(), server_default="false"),
    )

def downgrade():
    op.drop_table("ledger_entries")
```

---

## 2) Modelos
**`backend/app/db/models/ledger.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, Date, Numeric, Boolean
from app.db.base import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    date = Column(Date)
    description = Column(String)
    amount = Column(Numeric(16,2))
    category = Column(String)
    classified_by_ai = Column(Boolean, default=False)
```

---

## 3) Servicios
**IA contable** – `backend/app/services/ai_accounting.py`
```python
from app.db.models.ledger import LedgerEntry
from sqlalchemy.orm import Session
import random

CATEGORIES = ["Materiales","Mano de Obra","Servicios","Impuestos","Otros"]

def classify_entry_ai(db: Session, entry_id: int):
    e = db.get(LedgerEntry, entry_id)
    # Simulación ML: random, real via ai_bridge
    e.category = random.choice(CATEGORIES)
    e.classified_by_ai = True
    db.commit(); return e.category
```

**Multi-empresa histórico** – `backend/app/services/history.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice

def historical_comparison(db: Session, years: int=3):
    data = {}
    for y in range(years):
        data[str(2025-y)] = {
            "total_invoices": sum([float(i.amount or 0) for i in db.query(Invoice).all()]),
            "avg_days": 45  # dummy value
        }
    return data
```

**Cumplimiento tributario** – `backend/app/services/tax.py`
```python
import requests, os

SII_API = os.getenv("SII_API")
TESORERIA_API = os.getenv("TES_API")

def validate_invoice_with_sii(dte_number: str):
    r = requests.get(f"{SII_API}/validate/{dte_number}")
    return r.json()

def pay_tax(amount: float, tax_type: str):
    r = requests.post(f"{TESORERIA_API}/pay", json={"amount": amount, "type": tax_type})
    return r.json()
```

---

## 4) API
**IA contable** – `backend/app/api/v1/ai_accounting.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.ai_accounting import classify_entry_ai

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/classify/{entry_id}")
def classify(entry_id: int, db: Session = Depends(get_db)):
    return {"category": classify_entry_ai(db, entry_id)}
```

**Histórico** – `backend/app/api/v1/history.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.history import historical_comparison

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/multi")
def multi(years: int=3, db: Session = Depends(get_db)):
    return historical_comparison(db, years)
```

**Tributario** – `backend/app/api/v1/tax.py`
```python
from fastapi import APIRouter
from app.services.tax import validate_invoice_with_sii, pay_tax

router = APIRouter()

@router.get("/validate/{dte}")
def validate(dte: str):
    return validate_invoice_with_sii(dte)

@router.post("/pay")
def pay(amount: float, tax_type: str):
    return pay_tax(amount, tax_type)
```

---

## 5) UI Next.js
- `/ledger/[projectId]`: lista de movimientos + botón **Clasificar con IA**.
- `/history/multi`: gráfico comparativo por empresa/año.
- `/tax`: validar facturas (DTE) y registrar pago de impuestos.

**Componentes**
- `LedgerTable.tsx`: tabla movimientos con categorías IA.
- `HistoryChart.tsx`: líneas de evolución KPIs multi-empresa.
- `TaxPanel.tsx`: validación y pagos tributarios.

---

## 6) Integración OFITEC
- **IA contable**: motor via `ai_bridge`, mejora continua con dataset.
- **Histórico multi-empresa**: datos consolidados de invoices + cashflow.
- **Cumplimiento tributario**: conexión directa SII/Tesorería.
- **Auditoría**: cada clasificación o pago registrado en logs.

---

## 7) Checklist Sprint 19-20
- [ ] Migración 0010 aplicada.
- [ ] Clasificación AI de movimientos operativa.
- [ ] Comparativas históricas generadas.
- [ ] Validación SII y pagos Tesorería simulados.
- [ ] UI para ledger, history y tax.
- [ ] Tests Pytest cubriendo IA, histórico y tributario.
- [ ] Auditoría extendida funcionando.

---

## 8) Próximos pasos (Sprint 21+)
- Motor de predicciones tributarias (IVA, PPM, renta).
- Análisis de riesgos fiscales con IA.
- Reportes multi-empresa comparativos (holding-level insights).
- Integración con contabilidad internacional (IFRS).

