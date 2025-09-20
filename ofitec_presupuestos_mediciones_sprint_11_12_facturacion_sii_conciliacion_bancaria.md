# OFITEC · Presupuestos/Mediciones – Sprint 11-12

Este Sprint conecta directamente con **facturación electrónica SII (DTE)** y **conciliación bancaria automática**. Con esto, cerramos el flujo: Presupuesto → Certificación → Factura → Pago → Conciliación.

---

## 0) Objetivos
- **Facturación SII**: emitir y validar DTE desde certificaciones.
- **Conciliación bancaria**: integrar cartolas (Banco de Chile, Santander vía Fintoc) y cruzarlas con facturas y OCs.
- **Alertas**: discrepancias entre facturación y conciliación.
- **Auditoría**: todos los eventos registrados en `audit_logs`.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0006_invoices_bank.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0006_invoices_bank"
down_revision = "0005_certifications_cash_docs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cert_id", sa.Integer, sa.ForeignKey("certifications.id", ondelete="SET NULL")),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="SET NULL")),
        sa.Column("dte_number", sa.String()),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("amount", sa.Numeric(16,2)),
        sa.Column("xml_ref", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("date", sa.Date()),
        sa.Column("description", sa.String()),
        sa.Column("amount", sa.Numeric(16,2)),
        sa.Column("balance", sa.Numeric(16,2)),
        sa.Column("source", sa.String()),  # banco_chile|santander
        sa.Column("raw", sa.JSON()),
    )

def downgrade():
    op.drop_table("bank_transactions")
    op.drop_table("invoices")
```

---

## 2) Modelos
**`backend/app/db/models/invoice.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    cert_id = Column(Integer, ForeignKey("certifications.id", ondelete="SET NULL"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"))
    dte_number = Column(String)
    status = Column(String)
    amount = Column(Numeric(16,2))
    xml_ref = Column(String)
    created_at = Column(DateTime)
```

**`backend/app/db/models/bank.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, Date, Numeric, JSON
from app.db.base import Base

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    date = Column(Date)
    description = Column(String)
    amount = Column(Numeric(16,2))
    balance = Column(Numeric(16,2))
    source = Column(String)
    raw = Column(JSON)
```

---

## 3) Servicios
### Facturación SII (DTE)
**`backend/app/services/invoices.py`**
```python
import requests, os
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice

SII_URL = "https://palena.sii.cl/cgi_dte/dte/"  # sandbox
SII_USER = os.getenv("SII_USER")
SII_PASS = os.getenv("SII_PASS")

def create_invoice(db: Session, cert_id: int, supplier_id: int, amount: float, xml: str):
    inv = Invoice(cert_id=cert_id, supplier_id=supplier_id, amount=amount, status="pending", xml_ref=xml)
    db.add(inv); db.commit(); return inv.id

def send_to_sii(invoice_id: int, db: Session):
    inv = db.get(Invoice, invoice_id)
    # ejemplo simplificado: POST XML a SII
    files = {"dte": ("dte.xml", open(inv.xml_ref,"rb"), "application/xml")}
    r = requests.post(SII_URL, files=files, auth=(SII_USER,SII_PASS))
    if r.status_code==200:
        inv.status="accepted"
    else:
        inv.status="rejected"
    db.commit(); return inv.status
```

### Conciliación Bancaria
**`backend/app/services/bank.py`**
```python
from sqlalchemy.orm import Session
from app.db.models.bank import BankTransaction
from app.db.models.invoice import Invoice

def import_transactions(db: Session, project_id: int, txs: list[dict], source: str):
    for t in txs:
        db.add(BankTransaction(project_id=project_id, date=t["date"], description=t["desc"], amount=t["amount"], balance=t.get("balance",0), source=source, raw=t))
    db.commit(); return True

def reconcile(db: Session, project_id: int):
    invoices = db.query(Invoice).all()
    txs = db.query(BankTransaction).filter_by(project_id=project_id).all()
    matches, unmatched = [], []
    for inv in invoices:
        match = next((t for t in txs if abs(float(t.amount))==float(inv.amount)), None)
        if match:
            matches.append({"invoice": inv.id, "tx": match.id})
        else:
            unmatched.append(inv.id)
    return {"matches": matches, "unmatched": unmatched}
```

---

## 4) API
**Facturación** – `backend/app/api/v1/invoices.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.invoices import create_invoice, send_to_sii

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/create")
def create(cert_id: int, supplier_id: int, amount: float, xml: str, db: Session = Depends(get_db)):
    return {"invoice_id": create_invoice(db, cert_id, supplier_id, amount, xml)}

@router.post("/send/{invoice_id}")
def send(invoice_id: int, db: Session = Depends(get_db)):
    return {"status": send_to_sii(invoice_id, db)}
```

**Banco** – `backend/app/api/v1/bank.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bank import import_transactions, reconcile

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/import")
def import_(project_id: int, txs: list[dict], source: str, db: Session = Depends(get_db)):
    return {"ok": import_transactions(db, project_id, txs, source)}

@router.get("/{project_id}/reconcile")
def reconcile_(project_id: int, db: Session = Depends(get_db)):
    return reconcile(db, project_id)
```

---

## 5) UI Next.js
- `/invoices/[projectId]`: lista de certificaciones, botón **Emitir Factura**, estado (pendiente, aceptada, rechazada).
- `/bank/[projectId]`: subir cartola (CSV/Excel), ver conciliación (matches vs no conciliados).
- `/bank/reports`: resumen conciliado, diferencias, export Excel.

**Componentes**
- `InvoiceTable.tsx`: facturas con estado.
- `BankUpload.tsx`: carga de cartolas.
- `ReconcileView.tsx`: matches y pendientes.

---

## 6) Integración OFITEC
- **Invoices** sincronizadas con `project_financials` y auditoría.
- **BankTransactions** conectan con Fintoc (API cartolas Chile/Santander).
- **Conciliación** alimenta KPIs de flujo de caja.
- **Alertas** cuando hay facturas sin pago después de X días.

---

## 7) Checklist Sprint 11-12
- [ ] Migración 0006 aplicada.
- [ ] Creación y envío de facturas a SII.
- [ ] Estado de aceptación/rechazo guardado.
- [ ] Importación de cartolas (CSV/Fintoc API).
- [ ] Conciliación automática vs facturas.
- [ ] UI de facturas y conciliación visible.
- [ ] Tests Pytest para facturación y conciliación.
- [ ] Auditoría y alertas integradas.

---

## 8) Próximos pasos (Sprint 13+)
- Integración multi-banco (BICE, Itaú).
- Factoring automático (ofertas de financiamiento sobre facturas aceptadas).
- Simulación de flujo consolidado multi-proyecto.
- Dashboards ejecutivos: aging de facturas, días de pago promedio, KPIs financieros globales.

