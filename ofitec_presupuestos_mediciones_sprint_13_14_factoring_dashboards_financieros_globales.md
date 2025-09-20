# OFITEC · Presupuestos/Mediciones – Sprint 13-14

En este Sprint agregamos **factoring automático** y **dashboards financieros globales**. Con esto, Ofitec alcanza un nivel de gestión ejecutiva consolidada multi-proyecto.

---

## 0) Objetivos
- **Factoring automático**: integración con APIs de financiamiento para adelantar pagos sobre facturas aceptadas.
- **Dashboards globales**: visión consolidada de flujo de caja, aging de facturas, días promedio de pago, KPIs multi-proyecto.
- **Alertas ejecutivas**: indicadores críticos enviados a gerencia.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0007_factoring_dashboards.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0007_factoring_dashboards"
down_revision = "0006_invoices_bank"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "factoring_offers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id", ondelete="CASCADE")),
        sa.Column("provider", sa.String()),
        sa.Column("rate", sa.Numeric(6,3)),
        sa.Column("advance", sa.Numeric(16,2)),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("factoring_offers")
```

---

## 2) Modelos
**`backend/app/db/models/factoring.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric
from app.db.base import Base

class FactoringOffer(Base):
    __tablename__ = "factoring_offers"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"))
    provider = Column(String)
    rate = Column(Numeric(6,3))
    advance = Column(Numeric(16,2))
    status = Column(String)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Factoring** – `backend/app/services/factoring.py`
```python
import requests
from sqlalchemy.orm import Session
from app.db.models.factoring import FactoringOffer

FACTORING_API = "https://api.factoring-demo.com/offers"

def request_offers(db: Session, invoice_id: int, amount: float):
    # Simulación: consulta API externa
    r = requests.post(FACTORING_API, json={"invoice_id": invoice_id, "amount": amount})
    offers = r.json().get("offers", [])
    for o in offers:
        db.add(FactoringOffer(invoice_id=invoice_id, provider=o["provider"], rate=o["rate"], advance=o["advance"], status="offered"))
    db.commit()
    return offers

def accept_offer(db: Session, offer_id: int):
    offer = db.get(FactoringOffer, offer_id)
    offer.status = "accepted"
    db.commit(); return True
```

**Dashboards globales** – `backend/app/services/dashboards.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice
from app.db.models.bank import BankTransaction

def global_kpis(db: Session):
    invoices = db.query(Invoice).all()
    txs = db.query(BankTransaction).all()
    aging = {"0-30":0,"31-60":0,"61-90":0,">90":0}
    for inv in invoices:
        # simplificado: asignar aging random o por fecha creada
        aging["0-30"]+=float(inv.amount or 0)
    inflows = sum([float(t.amount) for t in txs if t.amount>0])
    outflows = sum([float(t.amount) for t in txs if t.amount<0])
    return {
        "total_invoices": len(invoices),
        "aging": aging,
        "cash_inflows": inflows,
        "cash_outflows": outflows,
        "net": inflows+outflows
    }
```

---

## 4) API
**Factoring** – `backend/app/api/v1/factoring.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.factoring import request_offers, accept_offer

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/offers")
def offers(invoice_id: int, amount: float, db: Session = Depends(get_db)):
    return request_offers(db, invoice_id, amount)

@router.post("/accept/{offer_id}")
def accept(offer_id: int, db: Session = Depends(get_db)):
    return {"ok": accept_offer(db, offer_id)}
```

**Dashboards** – `backend/app/api/v1/dashboards.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.dashboards import global_kpis

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/global")
def global_(db: Session = Depends(get_db)):
    return global_kpis(db)
```

---

## 5) UI Next.js
- `/factoring/[invoiceId]`: muestra ofertas recibidas y opción de aceptar.
- `/dashboards/global`: KPIs financieros multi-proyecto, gráficos aging, flujo neto.

**Componentes**
- `FactoringOffers.tsx`: tabla con proveedor, tasa, anticipo, estado.
- `GlobalKPIs.tsx`: cards (facturas, aging, cashflow).
- `CashFlowChart.tsx`: gráfico de barras inflows vs outflows.

---

## 6) Integración OFITEC
- **Factoring**: enlaza facturas aceptadas con financiamiento.
- **Dashboards**: consolidan datos de invoices, bank, cash, riesgos.
- **Alertas**: thresholds configurables (ej. aging > 60 días).
- **AI Bridge**: proyecciones de flujo de caja multi-proyecto.

---

## 7) Checklist Sprint 13-14
- [ ] Migración 0007 aplicada.
- [ ] Solicitud de ofertas de factoring desde facturas.
- [ ] Aceptación de ofertas y actualización de estado.
- [ ] KPIs globales calculados.
- [ ] UI de factoring y dashboards globales desplegada.
- [ ] Tests Pytest para factoring y dashboards.
- [ ] Integración con auditoría y alertas.

---

## 8) Próximos pasos (Sprint 15+)
- Reportes financieros exportables (Excel/PDF multi-proyecto).
- Simulador IA de factoring (mejor proveedor según perfil).
- Integración contable (ERP externo, contabilidad tributaria).
- Tablero ejecutivo con comparativas históricas y forecast.

