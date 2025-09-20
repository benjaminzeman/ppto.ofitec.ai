# OFITEC · Módulo Presupuestos/Mediciones (Segunda Parte)

Este archivo complementa la **estructura base** creada en el archivo anterior y añade:

1. CRUDs reales para modelos principales (FastAPI + SQLAlchemy).
2. Migraciones iniciales con Alembic.
3. Parser BC3 (borrador con tests).
4. Plantillas Excel reales para import/export.
5. Export PDF inicial de presupuesto.

---

## 1. CRUDs reales (FastAPI + SQLAlchemy)

**Ejemplo – **``

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas import budget as schemas

router = APIRouter()

@router.post("/projects", response_model=schemas.Project)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = models.Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/projects", response_model=list[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.post("/chapters", response_model=schemas.Chapter)
def create_chapter(payload: schemas.ChapterCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    chapter = models.Chapter(project_id=payload.project_id, code=payload.code, name=payload.name)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter
```

``

```python
from pydantic import BaseModel

class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    class Config:
        orm_mode = True

class ChapterBase(BaseModel):
    project_id: int
    code: str
    name: str

class ChapterCreate(ChapterBase):
    pass

class Chapter(ChapterBase):
    id: int
    class Config:
        orm_mode = True
```

---

## 2. Migraciones iniciales (Alembic)

``

```python
from alembic import op
import sqlalchemy as sa

revision = '20250919_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False)
    )
    op.create_table('chapters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE')),
        sa.Column('code', sa.String, index=True),
        sa.Column('name', sa.String)
    )
    op.create_table('items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('chapter_id', sa.Integer, sa.ForeignKey('chapters.id', ondelete='CASCADE')),
        sa.Column('code', sa.String),
        sa.Column('name', sa.String),
        sa.Column('unit', sa.String),
        sa.Column('quantity', sa.Numeric(16,3)),
        sa.Column('price', sa.Numeric(16,2))
    )

def downgrade():
    op.drop_table('items')
    op.drop_table('chapters')
    op.drop_table('projects')
```

---

## 3. Parser BC3 (borrador)

``

```python
import xml.etree.ElementTree as ET

# Simplificado: lee un archivo BC3 y devuelve estructura básica

def read_bc3(file_path: str):
    tree = ET.parse(file_path)
    root = tree.getroot()

    chapters, items, resources, apus = [], [], [], []

    for c in root.findall('.//Chapter'):
        chapters.append({
            'code': c.get('code'),
            'name': c.get('name')
        })
    for i in root.findall('.//Item'):
        items.append({
            'code': i.get('code'),
            'name': i.get('name'),
            'unit': i.get('unit'),
            'price': i.get('price')
        })
    # Recursos y APU por implementar

    return {
        'chapters': chapters,
        'items': items,
        'resources': resources,
        'apu': apus
    }
```

**Tests** – `backend/app/tests/test_bc3_parser.py`

```python
from app.services import bc3_parser

def test_read_bc3():
    data = bc3_parser.read_bc3('tests/data/sample.bc3')
    assert 'chapters' in data
    assert isinstance(data['chapters'], list)
```

---

## 4. Plantillas Excel (import/export)

``

```python
import pandas as pd

def export_budget_xlsx(project):
    data = []
    for ch in project.chapters:
        for it in ch.items:
            data.append({
                'Capítulo': ch.code,
                'PartidaCódigo': it.code,
                'PartidaNombre': it.name,
                'Unidad': it.unit,
                'Cantidad': float(it.quantity or 0),
                'PrecioUnitario': float(it.price or 0),
                'Total': float((it.quantity or 0) * (it.price or 0))
            })
    df = pd.DataFrame(data)
    path = f"export_budget_{project.id}.xlsx"
    df.to_excel(path, index=False)
    return path
```

**Plantilla mínima de columnas para import:**

- CapítuloCódigo
- CapítuloNombre
- PartidaCódigo
- PartidaNombre
- Unidad
- Cantidad
- PrecioUnitario

---

## 5. Export PDF inicial

``

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def export_budget_pdf(project):
    doc = SimpleDocTemplate(f"budget_{project.id}.pdf", pagesize=A4)
    data = [["Código", "Nombre", "Unidad", "Cantidad", "Precio Unit.", "Total"]]
    for ch in project.chapters:
        for it in ch.items:
            total = float((it.quantity or 0) * (it.price or 0))
            data.append([it.code, it.name, it.unit, it.quantity, it.price, total])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    elements = [table]
    doc.build(elements)
    return f"budget_{project.id}.pdf"
```

---

## 6. Próximos pasos (sprint 2 y 3)

- Completar parser BC3 con recursos + APU.
- Endpoint `/api/v1/imports/bc3` que procese archivo y cree objetos.
- UI en Next.js: carga BC3/Excel → barra progreso.
- Export comparativos (Excel/PDF).
- Agregar mediciones manuales en UI.

> Con este bloque ya tenemos CRUD funcional, migraciones iniciales y primeros servicios (Excel, PDF, BC3).

