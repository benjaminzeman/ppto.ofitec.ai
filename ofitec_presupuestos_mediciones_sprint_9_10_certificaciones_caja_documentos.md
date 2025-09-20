# OFITEC · Presupuestos/Mediciones – Sprint 9-10

En este Sprint incorporamos **Certificaciones de obra**, **Simulación de Caja** y **Control Documental**. Estos procesos consolidan la trazabilidad completa desde el presupuesto → avance → estado de pago → flujo financiero → documentación.

---

## 0) Objetivos

- **Certificaciones**: estados de pago basados en mediciones y versiones de presupuesto.
- **Simulación de Caja**: escenarios con riesgos, desvíos y compromisos (OC, facturas).
- **Control Documental**: contratos, adendas, minutas y anexos vinculados a proyectos/partidas.
- **Integración**: sincronizar con `project_financials` y auditoría.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0005_certifications_cash_docs"
down_revision = "0004_workflows_dashboards_risks"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("budget_versions.id", ondelete="SET NULL")),
        sa.Column("period", sa.String()),  # AAAA-MM
        sa.Column("status", sa.String(), server_default="draft"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_table(
        "certification_lines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cert_id", sa.Integer, sa.ForeignKey("certifications.id", ondelete="CASCADE")),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Numeric(16,3)),
        sa.Column("amount", sa.Numeric(16,2)),
    )

    op.create_table(
        "cash_scenarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("name", sa.String()),
        sa.Column("data", sa.JSON()),  # compromisos, riesgos, ingresos simulados
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("type", sa.String()),  # contrato|adenda|minuta
        sa.Column("name", sa.String()),
        sa.Column("file_ref", sa.String()),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("documents")
    op.drop_table("cash_scenarios")
    op.drop_table("certification_lines")
    op.drop_table("certifications")
```

---

## 2) Modelos

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric
from app.db.base import Base

class Certification(Base):
    __tablename__ = "certifications"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="SET NULL"))
    period = Column(String)
    status = Column(String)
    created_at = Column(DateTime)

class CertificationLine(Base):
    __tablename__ = "certification_lines"
    id = Column(Integer, primary_key=True)
    cert_id = Column(Integer, ForeignKey("certifications.id", ondelete="CASCADE"))
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"))
    qty = Column(Numeric(16,3))
    amount = Column(Numeric(16,2))
```

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON
from app.db.base import Base

class CashScenario(Base):
    __tablename__ = "cash_scenarios"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String)
    data = Column(JSON)
    created_at = Column(DateTime)
```

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    type = Column(String)
    name = Column(String)
    file_ref = Column(String)
    uploaded_at = Column(DateTime)
```

---

## 3) Servicios

**Certificaciones** – `backend/app/services/certifications.py`

```python
from sqlalchemy.orm import Session
from app.db.models.certification import Certification, CertificationLine
from app.db.models.budget import Item

def create_certification(db: Session, project_id: int, version_id: int, period: str, lines: list[dict]):
    cert = Certification(project_id=project_id, version_id=version_id, period=period, status="draft")
    db.add(cert); db.flush()
    total = 0
    for l in lines:
        it = db.get(Item, l["item_id"])
        amt = float(l["qty"])*float(it.price)
        db.add(CertificationLine(cert_id=cert.id, item_id=it.id, qty=l["qty"], amount=amt))
        total+=amt
    db.commit()
    return {"cert_id": cert.id, "total": total}
```

**Caja** – `backend/app/services/cash.py`

```python
from sqlalchemy.orm import Session
from app.db.models.cash import CashScenario

def create_scenario(db: Session, project_id: int, name: str, data: dict):
    sc = CashScenario(project_id=project_id, name=name, data=data)
    db.add(sc); db.commit(); return sc.id

def simulate_cashflow(db: Session, project_id: int):
    scs = db.query(CashScenario).filter_by(project_id=project_id).all()
    out = []
    for sc in scs:
        inflows = sum(sc.data.get("inflows", []))
        outflows = sum(sc.data.get("outflows", []))
        balance = inflows - outflows
        out.append({"scenario": sc.name, "balance": balance})
    return out
```

**Documentos** – `backend/app/services/documents.py`

```python
from sqlalchemy.orm import Session
from app.db.models.document import Document

def add_document(db: Session, project_id: int, type_: str, name: str, file_ref: str):
    d = Document(project_id=project_id, type=type_, name=name, file_ref=file_ref)
    db.add(d); db.commit(); return d.id

def list_documents(db: Session, project_id: int):
    return db.query(Document).filter_by(project_id=project_id).all()
```

---

## 4) API

**Certificaciones** – `backend/app/api/v1/certifications.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.certifications import create_certification

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/create")
def create(project_id: int, version_id: int, period: str, lines: list[dict], db: Session = Depends(get_db)):
    return create_certification(db, project_id, version_id, period, lines)
```

**Caja** – `backend/app/api/v1/cash.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.cash import create_scenario, simulate_cashflow

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/scenario")
def scenario(project_id: int, name: str, data: dict, db: Session = Depends(get_db)):
    return {"id": create_scenario(db, project_id, name, data)}

@router.get("/{project_id}/simulate")
def simulate(project_id: int, db: Session = Depends(get_db)):
    return simulate_cashflow(db, project_id)
```

**Documentos** – `backend/app/api/v1/documents.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.documents import add_document, list_documents

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/add")
def add(project_id: int, type_: str, name: str, file_ref: str, db: Session = Depends(get_db)):
    return {"doc_id": add_document(db, project_id, type_, name, file_ref)}

@router.get("/{project_id}")
def list_(project_id: int, db: Session = Depends(get_db)):
    return list_documents(db, project_id)
```

---

## 5) UI Next.js

- `/certifications/[projectId]`: crear certificación (selección de versión, periodo, partidas). Mostrar total y export PDF.
- `/cash/[projectId]`: lista de escenarios + gráfico de flujo (línea de balance). Comparar escenarios.
- `/documents/[projectId]`: subir/ver contratos, adendas, minutas. Previsualizar PDFs.

**Componentes**

- `CertForm.tsx`: formulario certificación.
- `CashChart.tsx`: gráfico con escenarios.
- `DocTable.tsx`: tabla de documentos con links a archivos.

---

## 6) Integración OFITEC

- **Certificaciones**: enlazadas con auditoría y export a `project_financials` (estado de pago → flujo caja).
- **Caja**: escenarios conectan con `ai_bridge` para simulaciones predictivas.
- **Documentos**: integrado con `docuchat` (búsqueda y consultas de IA sobre contratos).

---

## 7) Checklist de cierre Sprint 9-10

-

---

## 8) Próximos pasos (Sprint 11+)

- Flujo de facturación (DTE SII ↔ certificaciones).
- Integración bancaria (conciliación automática vs certificaciones).
- AI para simulación de escenarios de caja multi-proyecto.
- Control documental avanzado (versionado, firma digital).
- Tablero ejecutivo consolidado (KPIs globales, alertas).

