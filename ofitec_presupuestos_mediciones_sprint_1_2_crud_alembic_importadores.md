# OFITEC · Presupuestos/Mediciones – Sprint 1-2

Este archivo continúa el trabajo del MVP y agrega **CRUDs reales**, **migraciones Alembic**, **tests**, **plantillas Excel**, **parser BC3 (borrador)** y **export PDF**. Copia y pega los archivos según rutas.

---

## 0) Pre-requisitos rápidos

1. Tener levantada la base del repo del archivo anterior.
2. Crear BD y ejecutar la primera migración.

```bash
# desde /ofitec-budgets
cp .env.example .env
docker compose up -d --build
# crear tabla base con alembic (ver secciones 2 y 3)
```

---

## 1) Modelos (SQLAlchemy) – MVP Completo

**Ruta:** `backend/app/db/models/`

``

```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

``

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

``

```python
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    currency = Column(String, default="CLP")
```

``

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    code = Column(String, index=True)
    name = Column(String)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    code = Column(String, index=True)
    name = Column(String)
    unit = Column(String, default="m2")
    quantity = Column(Numeric(16,3), default=0)
    price = Column(Numeric(16,2), default=0)  # calculado a partir del APU

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    type = Column(String)  # MO, EQ, MAT, SUB
    code = Column(String, index=True)
    name = Column(String)
    unit = Column(String, default="u")
    unit_cost = Column(Numeric(16,4), default=0)

class APU(Base):
    __tablename__ = "apus"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="RESTRICT"))
    coeff = Column(Numeric(16,6), default=0)  # consumo por unidad de Item
```

``

```python
from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Text
from app.db.base import Base

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), index=True)
    source = Column(String, default="manual")  # manual|excel|ifc
    qty = Column(Numeric(16,3), default=0)
    note = Column(Text)
```

---

## 2) Alembic – Configuración y entorno

`` (plantilla mínima)

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    return os.getenv("DATABASE_URL")

target_metadata = None  # opcional: importar Base.metadata si usas autogenerate

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## 3) Migración inicial (crear tablas)

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), server_default="CLP"),
    )
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("code", sa.String()),
        sa.Column("name", sa.String()),
    )
    op.create_table(
        "items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapters.id", ondelete="CASCADE")),
        sa.Column("code", sa.String()),
        sa.Column("name", sa.String()),
        sa.Column("unit", sa.String(), server_default="m2"),
        sa.Column("quantity", sa.Numeric(16,3), server_default="0"),
        sa.Column("price", sa.Numeric(16,2), server_default="0"),
    )
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("type", sa.String()),
        sa.Column("code", sa.String()),
        sa.Column("name", sa.String()),
        sa.Column("unit", sa.String(), server_default="u"),
        sa.Column("unit_cost", sa.Numeric(16,4), server_default="0"),
    )
    op.create_table(
        "apus",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("resource_id", sa.Integer, sa.ForeignKey("resources.id", ondelete="RESTRICT")),
        sa.Column("coeff", sa.Numeric(16,6), server_default="0"),
    )
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(), server_default="manual"),
        sa.Column("qty", sa.Numeric(16,3), server_default="0"),
        sa.Column("note", sa.Text()),
    )

def downgrade():
    op.drop_table("measurements")
    op.drop_table("apus")
    op.drop_table("resources")
    op.drop_table("items")
    op.drop_table("chapters")
    op.drop_table("projects")
```

**Comandos**

```bash
# ejecutar migraciones
docker compose exec backend alembic upgrade head
```

---

## 4) Servicios – Lógica de APU y KPIs

``

```python
from decimal import Decimal

def compute_item_price(apulines: list[dict]) -> Decimal:
    """Suma(coeff * unit_cost) por línea de APU."""
    total = Decimal("0")
    for l in apulines:
        coeff = Decimal(str(l.get("coeff", 0)))
        unit_cost = Decimal(str(l.get("unit_cost", 0)))
        total += coeff * unit_cost
    return total.quantize(Decimal("0.01"))
```

---

## 5) API – CRUDs mínimos

`` (sustituir stub)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.session import SessionLocal
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from sqlalchemy.orm import Session
from app.services.kpis import compute_item_price

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProjectIn(BaseModel):
    name: str
    currency: str = "CLP"

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@router.post("/projects")
def create_project(p: ProjectIn, db: Session = Depends(get_db)):
    obj = Project(name=p.name, currency=p.currency)
    db.add(obj)
    db.commit(); db.refresh(obj)
    return obj

class ChapterIn(BaseModel):
    project_id: int
    code: str
    name: str

@router.post("/chapters")
def create_chapter(c: ChapterIn, db: Session = Depends(get_db)):
    obj = Chapter(**c.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

class ItemIn(BaseModel):
    chapter_id: int
    code: str
    name: str
    unit: str = "m2"
    quantity: float = 0

@router.post("/items")
def create_item(i: ItemIn, db: Session = Depends(get_db)):
    obj = Item(**i.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

class APULineIn(BaseModel):
    resource_code: str
    resource_name: str
    resource_type: str
    unit: str = "u"
    unit_cost: float
    coeff: float

@router.post("/items/{item_id}/apu")
def set_apu(item_id: int, lines: list[APULineIn], db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    # upsert resources + apu lines
    apu_payload = []
    for l in lines:
        r = db.query(Resource).filter(Resource.code==l.resource_code).first()
        if not r:
            r = Resource(code=l.resource_code, name=l.resource_name, type=l.resource_type, unit=l.unit, unit_cost=l.unit_cost)
            db.add(r); db.flush()
        apu = APU(item_id=item.id, resource_id=r.id, coeff=l.coeff)
        db.add(apu)
        apu_payload.append({"coeff": l.coeff, "unit_cost": l.unit_cost})
    # calcular precio unitario
    item.price = compute_item_price(apu_payload)
    db.commit(); db.refresh(item)
    return {"item_id": item.id, "price": str(item.price), "lines": len(lines)}
```

---

## 6) Importadores Excel (MVP)

``

```python
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU

BUDGET_COLUMNS = [
    "CapituloCodigo","CapituloNombre","PartidaCodigo","PartidaNombre","Unidad","Cantidad",
    "RecursoTipo","RecursoCodigo","RecursoNombre","Coef","CostoUnitRecurso"
]

def import_budget_xlsx(db: Session, file_path: str, project_name: str) -> int:
    df = pd.read_excel(file_path)
    df = df[BUDGET_COLUMNS]
    project = Project(name=project_name)
    db.add(project); db.flush()
    # agrupamos por capítulo/partida
    for (ccod, cnom, pcod, pnom, unit), g in df.groupby([
        "CapituloCodigo","CapituloNombre","PartidaCodigo","PartidaNombre","Unidad"
    ]):
        ch = Chapter(project_id=project.id, code=ccod, name=cnom)
        db.add(ch); db.flush()
        it = Item(chapter_id=ch.id, code=pcod, name=pnom, unit=unit, quantity=0, price=0)
        db.add(it); db.flush()
        apu_payload = []
        for _, row in g.iterrows():
            r = Resource(type=row.RecursoTipo, code=row.RecursoCodigo, name=row.RecursoNombre, unit="u", unit_cost=row.CostoUnitRecurso)
            db.add(r); db.flush()
            db.add(APU(item_id=it.id, resource_id=r.id, coeff=row.Coef))
            apu_payload.append({"coeff": row.Coef, "unit_cost": row.CostoUnitRecurso})
        from .kpis import compute_item_price
        it.price = compute_item_price(apu_payload)
    db.commit()
    return project.id

TEMPLATE_COLUMNS = BUDGET_COLUMNS
```

**Plantilla Excel** (columnas):

```
CapituloCodigo,CapituloNombre,PartidaCodigo,PartidaNombre,Unidad,Cantidad,RecursoTipo,RecursoCodigo,RecursoNombre,Coef,CostoUnitRecurso
```

---

## 7) Parser BC3 (borrador funcional)

``

```python
# Nota: BC3 tiene variantes. Este borrador asume un CSV derivado de BC3 o un parseo previo.
# Próximo sprint: lector real de .bc3 (texto) y normalización de capítulos/partidas/recursos.

import csv
from sqlalchemy.orm import Session
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from app.services.kpis import compute_item_price

FIELDS = [
  "CapituloCodigo","CapituloNombre","PartidaCodigo","PartidaNombre","Unidad","Cantidad",
  "RecursoTipo","RecursoCodigo","RecursoNombre","Coef","CostoUnitRecurso"
]

def import_bc3_csv(db: Session, csv_path: str, project_name: str) -> int:
    project = Project(name=project_name)
    db.add(project); db.flush()
    cache_ch = {}
    cache_it = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key_ch = (project.id, row["CapituloCodigo"])
            ch = cache_ch.get(key_ch)
            if not ch:
                ch = Chapter(project_id=project.id, code=row["CapituloCodigo"], name=row["CapituloNombre"])
                db.add(ch); db.flush(); cache_ch[key_ch] = ch
            key_it = (ch.id, row["PartidaCodigo"])
            it = cache_it.get(key_it)
            if not it:
                it = Item(chapter_id=ch.id, code=row["PartidaCodigo"], name=row["PartidaNombre"], unit=row["Unidad"], quantity=0, price=0)
                db.add(it); db.flush(); cache_it[key_it] = it
            r = Resource(type=row["RecursoTipo"], code=row["RecursoCodigo"], name=row["RecursoNombre"], unit="u", unit_cost=float(row["CostoUnitRecurso"]))
            db.add(r); db.flush()
            db.add(APU(item_id=it.id, resource_id=r.id, coeff=float(row["Coef"])) )
    # recalcular precios por item
    for it in db.query(Item).filter(Item.chapter_id.in_([c.id for c in cache_ch.values()])):
        apus = db.query(APU).filter(APU.item_id==it.id).all()
        lines = []
        for a in apus:
            r = db.get(Resource, a.resource_id)
            lines.append({"coeff": float(a.coeff), "unit_cost": float(r.unit_cost)})
        it.price = compute_item_price(lines)
    db.commit()
    return project.id
```

---

## 8) Export PDF (presupuesto básico)

``

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.db.models.budget import Chapter, Item

def export_budget_pdf(db: Session, project_id: int, dest_path: str):
    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Presupuesto Proyecto #{project_id}")
    y -= 30
    c.setFont("Helvetica", 10)
    for ch in db.query(Chapter).filter(Chapter.project_id==project_id).all():
        c.setFont("Helvetica-Bold", 11); c.drawString(40, y, f"{ch.code} — {ch.name}"); y -= 18
        for it in db.query(Item).filter(Item.chapter_id==ch.id).all():
            if y < 60:
                c.showPage(); y = height - 40
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"{it.code} {it.name} [{it.unit}]  Qty:{it.quantity}  PU:{it.price}")
            y -= 14
    c.showPage(); c.save()
```

**Dependencia**: agregar `reportlab` a `requirements.txt`.

---

## 9) Endpoints de import/export

``

```python
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.excel_io import import_budget_xlsx
from app.services.bc3_parser import import_bc3_csv
from app.services.pdf_export import export_budget_pdf
import tempfile, os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/excel")
async def import_excel(project_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        pid = import_budget_xlsx(db, tmp.name, project_name)
    os.unlink(tmp.name)
    return {"project_id": pid}

@router.post("/bc3csv")
async def import_bc3(project_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        pid = import_bc3_csv(db, tmp.name, project_name)
    os.unlink(tmp.name)
    return {"project_id": pid}

@router.get("/pdf/{project_id}")
def export_pdf(project_id: int, db: Session = Depends(get_db)):
    path = f"/tmp/budget_{project_id}.pdf"
    export_budget_pdf(db, project_id, path)
    return {"pdf_path": path}
```

---

## 10) Tests (Pytest)

``

```python
from app.services.kpis import compute_item_price

def test_compute_item_price():
    price = compute_item_price([
        {"coeff": 0.5, "unit_cost": 1000},
        {"coeff": 2, "unit_cost": 250.55},
    ])
    assert str(price) == "1001.10"
```

---

## 11) Frontend – Carga de Excel/BC3 y vista rápida

`` (simplificado)

```tsx
'use client'
import { useState } from 'react'

export default function UploadDialog() {
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('Proyecto Demo')

  const upload = async (endpoint: 'excel' | 'bc3csv') => {
    if (!file) return
    const fd = new FormData()
    fd.append('project_name', name)
    fd.append('file', file)
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/imports/${endpoint}`, {
      method: 'POST', body: fd
    })
    const data = await res.json()
    alert(`Proyecto importado: ${data.project_id}`)
  }

  return (
    <div className="flex gap-3 items-center">
      <input className="border p-2" value={name} onChange={e=>setName(e.target.value)} placeholder="Nombre del proyecto"/>
      <input type="file" onChange={e=>setFile(e.target.files?.[0] ?? null)} />
      <button className="border px-3 py-2" onClick={()=>upload('excel')}>Importar Excel</button>
      <button className="border px-3 py-2" onClick={()=>upload('bc3csv')}>Importar BC3 CSV</button>
    </div>
  )
}
```

``

```tsx
import UploadDialog from '@/components/UploadDialog'
export default function BudgetsPage(){
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Presupuestos</h1>
      <UploadDialog />
      {/* Próximo: tabla de proyectos y drilldown */}
    </div>
  )
}
```

---

## 12) Checklist de cierre Sprint 1-2

-

---

## 13) Próximo Sprint (3-4)

- **Mediciones** UI + valoración (curva S) y KPIs visibles.
- **Comparativos de compras** (carga Excel de proveedores, selector de mejor oferta y generación de OC PDF).
- **Versionado de presupuestos** (snapshot + diff visual por código, qty, PU).
- **Parser BC3 nativo** (lectura .bc3 real) y tolerancias.
- **Hardening**: validación de payloads, paginación y filtros, logs estructurados.

