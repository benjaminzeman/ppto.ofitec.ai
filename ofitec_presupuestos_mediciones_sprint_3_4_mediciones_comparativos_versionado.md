# OFITEC · Presupuestos/Mediciones – Sprint 3-4

Este archivo agrega **Mediciones (valoradas)**, **Comparativos de proveedores (OC MVP)** y **Versionado de presupuestos con diffs** sobre la base de Sprint 1–2. Incluye migraciones, modelos, endpoints, UI, algoritmos (Curva S y EVM básico) y pruebas.

---

## 0) Objetivos del Sprint

- **Mediciones**: captura manual / import Excel, consolidación y valoración automática por partida.
- **Curva S & EVM (PV/EV/AC)** simples por proyecto.
- **Comparativos**: carga de cotizaciones proveedor → ranking y selección → **Orden de Compra (OC) MVP**.
- **Versionado**: snapshots del presupuesto (v1, v2, …), diffs por código/cantidad/PU/total.
- **Reportes**: PDF/Excel (Curva S y Cuadro Comparativo).
- **Seguridad**: RBAC mínimo por proyecto (Admin, PM, Compras, Lectura).

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0002_measurements_comparatives_versions"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "measurement_batches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(), server_default="manual"),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.add_column("measurements", sa.Column("batch_id", sa.Integer, sa.ForeignKey("measurement_batches.id", ondelete="SET NULL")))

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("rut", sa.String()),
        sa.Column("email", sa.String()),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE")),
        sa.Column("file_ref", sa.String()),
        sa.Column("total", sa.Numeric(16,2), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "quote_lines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("quote_id", sa.Integer, sa.ForeignKey("quotes.id", ondelete="CASCADE")),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Numeric(16,3), server_default="0"),
        sa.Column("unit_price", sa.Numeric(16,2), server_default="0"),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE")),
        sa.Column("status", sa.String(), server_default="draft"),
        sa.Column("total", sa.Numeric(16,2), server_default="0"),
        sa.Column("pdf_ref", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("po_id", sa.Integer, sa.ForeignKey("purchase_orders.id", ondelete="CASCADE")),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Numeric(16,3), server_default="0"),
        sa.Column("unit_price", sa.Numeric(16,2), server_default="0"),
    )

    op.create_table(
        "budget_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("note", sa.Text()),
    )

    op.create_table(
        "budget_version_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("budget_versions.id", ondelete="CASCADE")),
        sa.Column("item_code", sa.String()),
        sa.Column("item_name", sa.String()),
        sa.Column("unit", sa.String()),
        sa.Column("qty", sa.Numeric(16,3), server_default="0"),
        sa.Column("unit_price", sa.Numeric(16,2), server_default="0"),
    )

def downgrade():
    op.drop_table("budget_version_items")
    op.drop_table("budget_versions")
    op.drop_table("purchase_order_lines")
    op.drop_table("purchase_orders")
    op.drop_table("quote_lines")
    op.drop_table("quotes")
    op.drop_table("suppliers")
    op.drop_column("measurements", "batch_id")
    op.drop_table("measurement_batches")
```

**Comando**

```bash
docker compose exec backend alembic upgrade head
```

---

## 2) Modelos (SQLAlchemy)

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Text, DateTime
from app.db.base import Base

class MeasurementBatch(Base):
    __tablename__ = "measurement_batches"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source = Column(String, default="manual")
    note = Column(Text)
    created_at = Column(DateTime)
```

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rut = Column(String)
    email = Column(String)

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    file_ref = Column(String)
    total = Column(Numeric(16,2))
    created_at = Column(DateTime)

class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id = Column(Integer, primary_key=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    qty = Column(Numeric(16,3))
    unit_price = Column(Numeric(16,2))

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    status = Column(String, default="draft")
    total = Column(Numeric(16,2))
    pdf_ref = Column(String)
    created_at = Column(DateTime)

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    qty = Column(Numeric(16,3))
    unit_price = Column(Numeric(16,2))
```

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, Text
from app.db.base import Base

class BudgetVersion(Base):
    __tablename__ = "budget_versions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime)
    note = Column(Text)

class BudgetVersionItem(Base):
    __tablename__ = "budget_version_items"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), index=True)
    item_code = Column(String)
    item_name = Column(String)
    unit = Column(String)
    qty = Column(Numeric(16,3))
    unit_price = Column(Numeric(16,2))
```

---

## 3) Servicios (Lógica)

``

```python
from sqlalchemy.orm import Session
from app.db.models.budget import Item
from app.db.models.measurement import Measurement

def project_measurements_summary(db: Session, project_id: int):
    # Suma qty medido por item del proyecto y valoriza
    rows = (
        db.query(Item.id, Item.code, Item.name, Item.unit, Item.price)
          .join("chapter")  # si defines relationship
    )
    # Simplificado: obtener measurements por item
    res = []
    for it in db.query(Item).join("chapter").filter_by(project_id=project_id).all():
        qty = sum([float(m.qty) for m in db.query(Measurement).filter(Measurement.item_id==it.id).all()])
        val = qty * float(it.price)
        res.append({"item_id": it.id, "code": it.code, "name": it.name, "unit": it.unit, "qty": qty, "unit_price": float(it.price), "value": val})
    return res
```

``

```python
from dataclasses import dataclass
from typing import List

@dataclass
class EVMPoint:
    period: str  # AAAA-MM
    PV: float
    EV: float
    AC: float

def compute_curve_s(budget_total_by_period: dict[str, float], earned_value_by_period: dict[str, float], actual_cost_by_period: dict[str, float]) -> List[EVMPoint]:
    periods = sorted(set(list(budget_total_by_period.keys()) + list(earned_value_by_period.keys()) + list(actual_cost_by_period.keys())))
    acc_pv = acc_ev = acc_ac = 0.0
    out = []
    for p in periods:
        acc_pv += float(budget_total_by_period.get(p, 0))
        acc_ev += float(earned_value_by_period.get(p, 0))
        acc_ac += float(actual_cost_by_period.get(p, 0))
        out.append(EVMPoint(p, round(acc_pv,2), round(acc_ev,2), round(acc_ac,2)))
    return out
```

``

```python
from sqlalchemy.orm import Session
from app.db.models.versions import BudgetVersion, BudgetVersionItem
from app.db.models.budget import Item

def create_budget_snapshot(db: Session, project_id: int, name: str, note: str | None=None) -> int:
    v = BudgetVersion(project_id=project_id, name=name, note=note)
    db.add(v); db.flush()
    for it in db.query(Item).join("chapter").filter_by(project_id=project_id).all():
        db.add(BudgetVersionItem(version_id=v.id, item_code=it.code, item_name=it.name, unit=it.unit, qty=it.quantity, unit_price=it.price))
    db.commit()
    return v.id

def diff_versions(db: Session, v_from: int, v_to: int):
    A = db.query(BudgetVersionItem).filter_by(version_id=v_from).all()
    B = db.query(BudgetVersionItem).filter_by(version_id=v_to).all()
    mapA = { (a.item_code): a for a in A }
    mapB = { (b.item_code): b for b in B }
    added, removed, changed = [], [], []
    for code in mapB.keys() - mapA.keys():
        b = mapB[code]; added.append(code)
    for code in mapA.keys() - mapB.keys():
        a = mapA[code]; removed.append(code)
    for code in mapA.keys() & mapB.keys():
        a, b = mapA[code], mapB[code]
        if (a.qty != b.qty) or (a.unit_price != b.unit_price):
            changed.append({
                "code": code,
                "qty_from": float(a.qty), "qty_to": float(b.qty),
                "pu_from": float(a.unit_price), "pu_to": float(b.unit_price),
                "delta_total": float(b.qty*b.unit_price - a.qty*a.unit_price)
            })
    return {"added": added, "removed": removed, "changed": changed}
```

``

```python
from sqlalchemy.orm import Session
from decimal import Decimal
from app.db.models.procurement import Quote, QuoteLine, PurchaseOrder, PurchaseOrderLine

def rank_quotes(db: Session, project_id: int):
    quotes = db.query(Quote).filter(Quote.project_id==project_id).all()
    out = []
    for q in quotes:
        lines = db.query(QuoteLine).filter(QuoteLine.quote_id==q.id).all()
        total = sum([float(l.qty)*float(l.unit_price) for l in lines])
        q.total = Decimal(str(total)); db.add(q)
        out.append({"quote_id": q.id, "supplier_id": q.supplier_id, "total": total})
    db.commit()
    out.sort(key=lambda x: x["total"])  # menor precio primero
    return out

def create_po_from_quote(db: Session, quote_id: int) -> int:
    q = db.get(Quote, quote_id)
    po = PurchaseOrder(project_id=q.project_id, supplier_id=q.supplier_id, status="draft", total=q.total)
    db.add(po); db.flush()
    for l in db.query(QuoteLine).filter_by(quote_id=q.id).all():
        db.add(PurchaseOrderLine(po_id=po.id, item_id=l.item_id, qty=l.qty, unit_price=l.unit_price))
    db.commit()
    return po.id
```

---

## 4) API (Endpoints)

`` (nuevo)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.measurements import project_measurements_summary

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{project_id}/summary")
def summary(project_id: int, db: Session = Depends(get_db)):
    return project_measurements_summary(db, project_id)
```

``

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.versioning import create_budget_snapshot, diff_versions

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{project_id}/snapshot")
def snapshot(project_id: int, name: str, note: str | None = None, db: Session = Depends(get_db)):
    vid = create_budget_snapshot(db, project_id, name, note)
    return {"version_id": vid}

@router.get("/diff")
def diff(v_from: int, v_to: int, db: Session = Depends(get_db)):
    return diff_versions(db, v_from, v_to)
```

``

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.comparatives import rank_quotes, create_po_from_quote

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{project_id}/rank")
def rank(project_id: int, db: Session = Depends(get_db)):
    return rank_quotes(db, project_id)

@router.post("/po")
def make_po(quote_id: int, db: Session = Depends(get_db)):
    po_id = create_po_from_quote(db, quote_id)
    return {"po_id": po_id}
```

> **Recuerda** registrar estos routers en `app.main`.

---

## 5) Plantillas Excel/PDF

**Excel – Cotizaciones (import)**

```
Proveedor, RUT, Email, PartidaCodigo, Cantidad, PrecioUnit
```

**PDF – Cuadro Comparativo**: generar tabla (Proveedor vs Total) + top 3 por menor precio + brecha vs presupuesto.

`` (stub)

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def comparative_pdf(dest_path: str, project_name: str, rows: list[dict]):
    c = canvas.Canvas(dest_path, pagesize=A4)
    y = A4[1]-40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40,y, f"Cuadro Comparativo – {project_name}")
    y -= 24
    c.setFont("Helvetica", 10)
    for r in rows[:50]:
        c.drawString(40,y, f"Supplier {r['supplier_id']} – Total: {r['total']}"); y -= 14
        if y < 60: c.showPage(); y = A4[1]-40
    c.showPage(); c.save()
```

---

## 6) UI Next.js (páginas nuevas)

**Rutas**

- `/measurements/[projectId]`: tabla consolidada (qty, PU, valor) + import Excel.
- `/comparatives/[projectId]`: carga Excel de cotizaciones + ranking + botón “Generar OC”.
- `/budgets/versions/[projectId]`: crear snapshot + visualizar diff (added/removed/changed).

**Componentes**

- `MeasurementsTable.tsx`: tabla con totales por partida.
- `ComparativeTable.tsx`: tabla de proveedores (por total) + gaps vs presupuesto.
- `VersionDiff.tsx`: lista de cambios con badges (↑↓) y delta\_total.

`` (simplificado)

```tsx
'use client'
export default function VersionDiff({data}:{data:any}){
  return (
    <div className="space-y-3">
      <section>
        <h3 className="font-semibold">Agregados ({data.added.length})</h3>
        <ul className="list-disc ml-6">{data.added.map((c:string)=>(<li key={c}>{c}</li>))}</ul>
      </section>
      <section>
        <h3 className="font-semibold">Eliminados ({data.removed.length})</h3>
        <ul className="list-disc ml-6">{data.removed.map((c:string)=>(<li key={c}>{c}</li>))}</ul>
      </section>
      <section>
        <h3 className="font-semibold">Cambiados ({data.changed.length})</h3>
        <table className="w-full border">
          <thead><tr><th>Código</th><th>Qty (from→to)</th><th>PU (from→to)</th><th>Δ Total</th></tr></thead>
          <tbody>
            {data.changed.map((r:any)=>(
              <tr key={r.code} className="border-t">
                <td>{r.code}</td>
                <td>{r.qty_from}→{r.qty_to}</td>
                <td>{r.pu_from}→{r.pu_to}</td>
                <td>{r.delta_total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
```

---

## 7) Importador Excel de Cotizaciones (Backend)

``

```python
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models.procurement import Supplier, Quote, QuoteLine
from app.db.models.budget import Item

QUOTE_COLUMNS = ["Proveedor","RUT","Email","PartidaCodigo","Cantidad","PrecioUnit"]

def import_quotes_xlsx(db: Session, file_path: str, project_id: int) -> int:
    df = pd.read_excel(file_path)
    df = df[QUOTE_COLUMNS]
    # agrupar por proveedor
    for (name, rut, email), g in df.groupby(["Proveedor","RUT","Email"]):
        s = db.query(Supplier).filter_by(name=name).first() or Supplier(name=name, rut=rut, email=email)
        db.add(s); db.flush()
        q = Quote(project_id=project_id, supplier_id=s.id, file_ref="")
        db.add(q); db.flush()
        for _, r in g.iterrows():
            it = db.query(Item).filter_by(code=r.PartidaCodigo).first()
            if not it: continue
            db.add(QuoteLine(quote_id=q.id, item_id=it.id, qty=r.Cantidad, unit_price=r.PrecioUnit))
    db.commit()
    return 1
```

**Endpoint** `POST /api/v1/purchases/quotes/import`

```python
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.quotes_excel import import_quotes_xlsx
import tempfile, os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/import")
async def import_quotes(project_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await file.read()); tmp.flush()
        import_quotes_xlsx(db, tmp.name, project_id)
    os.unlink(tmp.name)
    return {"ok": True}
```

---

## 8) Seguridad (roles mínimos)

- **Admin**: todo.
- **PM**: ver/editar mediciones y snapshots; ver comparativos.
- **Compras**: importar cotizaciones, generar **OC**.
- **Lectura**: ver dashboards y reportes.

Futuro: tabla `user_project_roles(user_id, project_id, role)` y dependencias en endpoints.

---

## 9) Pruebas (Pytest)

**Versionado** `backend/app/tests/test_versions.py`

```python
from app.services.versioning import diff_versions

def test_diff_versions(db_seed_two_versions):
    d = diff_versions(db_seed_two_versions, 1, 2)
    assert set(d.keys())=={"added","removed","changed"}
```

**Comparativos** `backend/app/tests/test_comparatives.py`

```python
from app.services.comparatives import rank_quotes

def test_rank_quotes(db_seed_quotes):
    r = rank_quotes(db_seed_quotes, project_id=1)
    assert r and r[0]['total'] <= r[-1]['total']
```

**Mediciones** `backend/app/tests/test_measurements.py`

```python
from app.services.measurements import project_measurements_summary

def test_measurements_summary(db_seed_measurements):
    res = project_measurements_summary(db_seed_measurements, 1)
    assert isinstance(res, list) and 'value' in res[0]
```

---

## 10) Reportes (Curva S y Comparativo)

- **Curva S**: usar `compute_curve_s()` con series mensuales (YYYY-MM). Exportar a PDF o Excel (pandas → xlsxwriter).
- **Comparativo**: PDF con ranking (Top 3) + ahorro vs presupuesto.

---

## 11) Checklist de Cierre Sprint 3–4

-

---

## 12) Notas de Integración con OFITEC (core/financials)

- **Sincronizar** `PurchaseOrder` → OFITEC `project_financials` para previsión de caja.
- **DTE/SII** (futuro): asociar OC → factura → estado de pago.
- **WhatsApp** (futuro): alertas de desvíos y adjudicación.

> Con esto queda desplegable el **núcleo operativo** de mediciones, comparativos y versionado. El siguiente paso es Sprint 5–6 (auditoría fina, RBAC por proyecto, BIM-IFC real, alertas y QA).

