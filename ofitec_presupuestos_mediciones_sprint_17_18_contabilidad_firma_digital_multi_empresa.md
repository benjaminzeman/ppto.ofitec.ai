# OFITEC · Presupuestos/Mediciones – Sprint 17-18

En este Sprint se aborda la **integración contable tributaria**, la **firma digital** de reportes/documentos y el **dashboard ejecutivo multi-empresa**.

---

## 0) Objetivos
- **Contabilidad tributaria**: integración con ERP externo (ej. Defontana, Nubox) vía API.
- **Firma digital**: aplicar firma electrónica avanzada a reportes/documentos.
- **Dashboard multi-empresa**: KPIs financieros agregados a nivel holding.
- **Seguridad**: trazabilidad legal de documentos y facturas.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0009_accounting_signing_multi.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0009_accounting_signing_multi"
down_revision = "0008_reports_ai_forecast"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "erp_integrations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE")),
        sa.Column("erp_name", sa.String()),
        sa.Column("api_key", sa.String()),
        sa.Column("base_url", sa.String()),
    )

    op.create_table(
        "signatures",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("doc_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Integer),
        sa.Column("signature_ref", sa.String()),
        sa.Column("signed_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("signatures")
    op.drop_table("erp_integrations")
```

---

## 2) Modelos
**`backend/app/db/models/erp.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String
from app.db.base import Base

class ERPIntegration(Base):
    __tablename__ = "erp_integrations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    erp_name = Column(String)
    api_key = Column(String)
    base_url = Column(String)
```

**`backend/app/db/models/signature.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from app.db.base import Base

class Signature(Base):
    __tablename__ = "signatures"
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    user_id = Column(Integer)
    signature_ref = Column(String)
    signed_at = Column(DateTime)
```

---

## 3) Servicios
**Contabilidad** – `backend/app/services/accounting.py`
```python
import requests
from app.db.models.erp import ERPIntegration

def push_invoice_to_erp(erp: ERPIntegration, invoice: dict):
    url = f"{erp.base_url}/invoices"
    headers = {"Authorization": f"Bearer {erp.api_key}"}
    return requests.post(url, json=invoice, headers=headers).json()
```

**Firma digital** – `backend/app/services/signature.py`
```python
import requests, os
from app.db.models.signature import Signature
from sqlalchemy.orm import Session

SIGN_API = os.getenv("SIGN_API")

# Simulación: usa proveedor de firma digital (ej. FirmaGob, eSign)
def sign_document(db: Session, doc_id: int, user_id: int, file_path: str):
    r = requests.post(SIGN_API, files={"file": open(file_path,"rb")})
    sig_ref = r.json().get("signature_id")
    s = Signature(doc_id=doc_id, user_id=user_id, signature_ref=sig_ref)
    db.add(s); db.commit(); return sig_ref
```

**Dashboard Multi-empresa** – `backend/app/services/multicompany.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice
from app.db.models.bank import BankTransaction

# Consolidar todas las empresas

def global_dashboard(db: Session):
    invs = db.query(Invoice).all()
    txs = db.query(BankTransaction).all()
    total = sum([float(i.amount or 0) for i in invs])
    inflows = sum([float(t.amount) for t in txs if t.amount>0])
    outflows = sum([float(t.amount) for t in txs if t.amount<0])
    return {"total_invoices": total, "cash_inflows": inflows, "cash_outflows": outflows, "net": inflows+outflows}
```

---

## 4) API
**Contabilidad** – `backend/app/api/v1/accounting.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.erp import ERPIntegration
from app.services.accounting import push_invoice_to_erp

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/push")
def push(erp_id: int, invoice: dict, db: Session = Depends(get_db)):
    erp = db.get(ERPIntegration, erp_id)
    return push_invoice_to_erp(erp, invoice)
```

**Firma digital** – `backend/app/api/v1/signature.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.signature import sign_document
import tempfile

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/sign")
def sign(doc_id: int, user_id: int, file_path: str, db: Session = Depends(get_db)):
    return {"signature": sign_document(db, doc_id, user_id, file_path)}
```

**Dashboard multi-empresa** – `backend/app/api/v1/multicompany.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.multicompany import global_dashboard

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/global")
def global_(db: Session = Depends(get_db)):
    return global_dashboard(db)
```

---

## 5) UI Next.js
- `/accounting`: exportar facturas a ERP externo.
- `/documents/sign`: botón **Firmar Digitalmente**.
- `/dashboards/multi`: visión consolidada (todas las empresas).

**Componentes**
- `ERPExport.tsx`: formulario exportación facturas.
- `SignButton.tsx`: acción firmar documento.
- `MultiDashboard.tsx`: KPIs consolidados multi-empresa.

---

## 6) Integración OFITEC
- **Contabilidad**: conecta facturas aceptadas con ERP tributario.
- **Firma digital**: asegura validez legal de documentos y reportes.
- **Dashboard multi-empresa**: visión global para directorio.
- **Auditoría**: registra todas las exportaciones y firmas.

---

## 7) Checklist Sprint 17-18
- [ ] Migración 0009 aplicada.
- [ ] ERP externo integrado (mock/test API).
- [ ] Firma digital aplicada en documentos.
- [ ] Dashboard multi-empresa operativo.
- [ ] UI de exportación, firma y dashboard creada.
- [ ] Tests Pytest de contabilidad, firma y multi.
- [ ] Auditoría registrada en logs.

---

## 8) Próximos pasos (Sprint 19+)
- IA contable (clasificación automática de gastos/ingresos).
- Firma digital avanzada con biometría.
- Comparativas multi-empresa históricas.
- Integración con Tesorería y SII para cumplimiento tributario completo.

