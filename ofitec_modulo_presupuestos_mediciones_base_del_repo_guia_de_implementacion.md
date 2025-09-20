# OFITEC · Módulo Presupuestos/Mediciones

Este documento incluye **(A)** la estructura base del repositorio (con archivos iniciales listos para copiar/pegar) y **(B)** una guía ordenada para implementar el módulo paso a paso.

---

## A) Estructura base del repositorio (MVP ejecutable)

> Stack: **Next.js 14** (frontend) + **FastAPI** (backend) + **PostgreSQL** + **Redis** + **RQ** (workers) + **S3/Local** para adjuntos. Todo orquestado con **Docker Compose**.

```
/ofitec-budgets
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── budgets.py
│   │   │   │   ├── measurements.py
│   │   │   │   ├── imports.py
│   │   │   │   ├── purchases.py
│   │   │   │   └── auth.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── project.py
│   │   │       ├── budget.py
│   │   │       ├── resource.py
│   │   │       ├── measurement.py
│   │   │       ├── versions.py
│   │   │       ├── procurement.py
│   │   │       └── certification.py
│   │   ├── schemas/
│   │   │   ├── budget.py
│   │   │   ├── measurement.py
│   │   │   ├── common.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── bc3_parser.py
│   │   │   ├── excel_io.py
│   │   │   ├── ifc_mapper.py
│   │   │   └── kpis.py
│   │   ├── workers/
│   │   │   ├── rq_worker.py
│   │   │   └── jobs.py
│   │   └── tests/
│   │       └── test_budgets.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic/
│       ├── env.py
│       └── versions/  (migraciones)
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── budgets/
│   │   │   ├── page.tsx
│   │   │   └── editor/
│   │   │       └── page.tsx
│   │   ├── measurements/page.tsx
│   │   ├── purchases/page.tsx
│   │   └── certifications/page.tsx
│   ├── components/
│   │   ├── BudgetTable.tsx
│   │   ├── APUEditor.tsx
│   │   ├── DiffViewer.tsx
│   │   ├── UploadDialog.tsx
│   │   └── KPICard.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── config.ts
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
└── scripts/
    ├── dev.sh
    └── seed_demo.py
```

### 1) `docker-compose.yml`

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ofitec
      POSTGRES_USER: ofitec
      POSTGRES_PASSWORD: ofitec
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  backend:
    build: ./backend
    env_file: .env
    depends_on: [db, redis]
    ports: ["5555:5555"]
    volumes: ["./backend/app:/app/app"]
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5555", "--reload"]

  worker:
    build: ./backend
    env_file: .env
    depends_on: [backend, redis]
    command: ["python", "-m", "app.workers.rq_worker"]

  frontend:
    build: ./frontend
    env_file: .env
    depends_on: [backend]
    ports: ["3001:3000"]
    volumes: ["./frontend:/app"]
    command: ["npm", "run", "dev"]

volumes:
  pgdata:
```

### 2) `.env.example`

```
# Backend
DATABASE_URL=postgresql+psycopg2://ofitec:ofitec@db:5432/ofitec
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change_me
ALLOWED_ORIGINS=http://localhost:3001

# Frontend
NEXT_PUBLIC_API_BASE=http://localhost:5555
```

### 3) Backend FastAPI

``

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
SQLAlchemy==2.0.34
alembic==1.13.2
psycopg2-binary==2.9.9
python-jose==3.3.0
passlib[bcrypt]==1.7.4
redis==5.0.8
rq==1.16.2
pandas==2.2.2
openpyxl==3.1.5
```

`` (mínimo funcional)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import budgets, measurements, imports, purchases, auth

app = FastAPI(title="OFITEC Budgets API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["budgets"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["measurements"])
app.include_router(imports.router, prefix="/api/v1/imports", tags=["imports"])
app.include_router(purchases.router, prefix="/api/v1/purchases", tags=["purchases"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Modelo de datos mínimo (ejemplo)** – `backend/app/db/models/budget.py`

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    code = Column(String, index=True)
    name = Column(String)

class Item(Base):  # Partida
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"))
    code = Column(String, index=True)
    name = Column(String)
    unit = Column(String, default="m2")
    quantity = Column(Numeric(16, 3), default=0)
    price = Column(Numeric(16, 2), default=0)

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    type = Column(String)  # MO, EQ, MAT, SUB
    code = Column(String)
    name = Column(String)
    unit_cost = Column(Numeric(16, 4))

class APU(Base):  # Descomposición de Item
    __tablename__ = "apus"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    coeff = Column(Numeric(16, 6))  # consumo por unidad de item
```

**Endpoints esenciales (borrador OpenAPI)** – `backend/app/api/v1/budgets.py`

```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/projects")
def list_projects():
    return []

@router.post("/projects")
def create_project(payload: dict):
    return payload

@router.get("/projects/{project_id}/chapters")
def list_chapters(project_id: int):
    return []

@router.post("/items")
def create_item(item: dict):
    return item

@router.post("/items/{item_id}/apu")
def set_apu(item_id: int, lines: list[dict]):
    return {"item_id": item_id, "lines": lines}
```

### 4) Frontend Next.js (estructura mínima)

``

```json
{
  "name": "ofitec-budgets-ui",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.7",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "zod": "3.23.8",
    "axios": "1.7.7"
  }
}
```

`` (stub del editor APU)

```tsx
'use client'
import { useEffect, useState } from 'react'
import axios from 'axios'

export default function APUEditor() {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => {
    axios.get(process.env.NEXT_PUBLIC_API_BASE + '/api/v1/budgets/projects')
      .then(() => setItems([]))
  }, [])
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Editor de APU</h1>
      {/* Tabla editable + atajos teclado (próximo sprint) */}
    </div>
  )
}
```

### 5) Importadores (placeholders)

- `services/bc3_parser.py`: funciones `read_bc3(file)` → devuelve estructura `{chapters, items, resources, apu}`.
- `services/excel_io.py`: funciones `export_budget_xlsx(project_id)`, `import_budget_xlsx(file)`.
- `services/ifc_mapper.py`: `map_ifc_to_items(ifc_file, rules)`.

### 6) Migraciones y seed

- Alembic inicial con tablas `projects, chapters, items, resources, apus`.
- `scripts/seed_demo.py` crea un proyecto demo con 2 capítulos y 3 partidas.

### 7) Comandos

```
# 1) Copiar .env
cp .env.example .env

# 2) Levantar todo
docker compose up --build -d

# 3) Probar
curl http://localhost:5555/health

# 4) Frontend en http://localhost:3001
```

---

## B) Guía ordenada de implementación

### Objetivo del Módulo

Construir **Presupuestos + Mediciones + Control base** con interoperabilidad (**BC3, Excel**) y versión inicial de **comparativos/OC**. Arquitectura API-first para evolucionar a certificaciones, control financiero y BIM.

### 1. Roadmap por Sprints (alta prioridad → baja)

**Sprint 0 – Infra & Esqueleto**

- Docker Compose, FastAPI, Next.js, Postgres, Redis, RQ.
- Alembic inicial + seed.
- Healthcheck, CORS, logging básico.

**Sprint 1 – Núcleo Presupuesto/APU**

- CRUD: Proyecto, Capítulo, Partida, Recurso.
- APU (MO/EQ/MAT/SUB) con coeficientes y cálculo de precio.
- Export **Excel** (plantilla estándar) y **PDF** básico.
- Dif de versiones (v0.1: duplicar presupuesto y comparar por código/costo).

**Sprint 2 – Importadores**

- Import **Excel** → crea/actualiza capítulos, partidas, APU.
- Import **BC3** (parser robusto con tests y archivos reales).
- Jobs en segundo plano + barra de progreso en UI.

**Sprint 3 – Mediciones**

- Estructura de mediciones por partida (manual + Excel).
- Valoración automática (curva S simple: qty \* precio unitario).
- KPIs proyecto: % avance físico y valorizado, desvío.

**Sprint 4 – Comparativos & Compras (MVP)**

- Solicitud de cotizaciones a proveedores.
- Carga de cotizaciones (Excel) y comparador por partida/recurso.
- Generación de **OC** (sin inventario aún) + export PDF.

**Sprint 5 – Seguridad & Auditoría**

- RBAC por proyecto (roles: Admin, PM, Compras, Lectura).
- Trail de auditoría: quién cambió qué/cuándo (items/APU/mediciones).

**Sprint 6 – BIM/IFC (Exploratorio)**

- Prototipo de mapeo IFC → partidas (reglas por clase/propiedades).
- PoC con 1 modelo y 10 reglas.

### 2. Definición de Hecho (DoD) por entregable clave

- **CRUD APU**: crear/editar/borrar líneas, recalcular precio unitario, tests unitarios.
- **Export Excel**: abrir en Excel/Google Sheets, columnas con código, nombre, unidad, cantidad, precio, desglose APU.
- **Import Excel**: idem; idempotente (reimportar actualiza sin duplicar).
- **Import BC3**: soporta variantes de codificación y catálogos; tests con 3 archivos reales.
- **Mediciones**: vista editable + sumarios; KPIs visibles en Dashboard.
- **Comparativos**: mostrar diferencia vs. presupuesto, mejor oferta por línea, totales.

### 3. Modelo de Datos (MVP)

- `projects(id, name, currency)`
- `chapters(id, project_id, code, name)`
- `items(id, chapter_id, code, name, unit, quantity, price)`
- `resources(id, type, code, name, unit_cost)`
- `apus(id, item_id, resource_id, coeff)`
- `measurements(id, item_id, source, qty, note)`
- `versions(id, project_id, name, created_at)` (futuro inmediato)
- `comparatives(id, project_id, supplier, total, file_ref)` (futuro inmediato)

### 4. Endpoints (catálogo)

- `GET /api/v1/budgets/projects`
- `POST /api/v1/budgets/projects`
- `GET /api/v1/budgets/{projectId}/chapters`
- `POST /api/v1/budgets/chapters`
- `POST /api/v1/budgets/items`
- `POST /api/v1/budgets/items/{itemId}/apu`
- `GET /api/v1/measurements/{projectId}` / `POST` mediciones
- `POST /api/v1/imports/excel` / `POST /api/v1/imports/bc3`
- `GET /api/v1/purchases/comparatives/{projectId}` (MVP)

### 5. UX (pautas rápidas)

- **Editor APU**: tabla con edición inline, atajos (Enter=abajo, Tab=derecha), agregación de recursos con `+`.
- **Diff de versiones**: códigos iguales → resaltar variación de precio/qty; códigos nuevos/eliminados con color.
- **Cargas masivas**: siempre con barra de progreso y log de resultados (creados/actualizados/errores).
- **KPIs**: 4 tarjetas (Costo Presupuestado, Costo APU recalculado, Avance Valorizado, Desvío).

### 6. Integraciones futuras (encaje con OFITEC)

- **SII / DTE**: validación de estados de pago y facturas.
- **Bancos (Fintoc)**: cashflow real por proyecto; conciliación.
- **WhatsApp**: alertas de desvíos y avances.
- **Odoo/OFITEC**: sincronizar proyectos/partners, o desplegar este módulo como servicio independiente y consumirlo desde tu portal.

### 7. Calidad, Pruebas y Observabilidad

- **Tests** Pytest (modelos y endpoints críticos).
- **Alembic** obligatorio por cambio de esquema.
- **Prometheus/Grafana** (reutilizable de tu stack) + logs JSON.

### 8. Seguridad

- JWT + refresco.
- RBAC por proyecto.
- Auditoría (tablas \*\_audit o triggers).

### 9. Plantillas Excel (columnas mínimas)

- **Presupuesto**: `CapítuloCódigo, CapítuloNombre, PartidaCódigo, PartidaNombre, Unidad, Cantidad, RecursoTipo, RecursoCódigo, RecursoNombre, Coef, CostoUnitRecurso`.
- **Mediciones**: `PartidaCódigo, Cantidad, Fuente, Nota`.

### 10. Riesgos y mitigación

- **Dialectos BC3** → parser con tolerancias y mapeos configurables.
- **Rendimiento** → índices por `project_id` y `code`, caché en Redis, jobs.
- **Cambio cultural** → reportes idénticos a tus formatos actuales.

---

## Anexos rápidos

- **README** (arranque): `docker compose up -d` y abrir `http://localhost:3001`.
- **Seed**: `docker compose exec backend python scripts/seed_demo.py`.
- **Variables**: copiar `.env.example` → `.env`.

> Con esto puedes **clonar/pegar** y levantar el MVP vacío. En los siguientes pasos completamos CRUDs, importadores y UI del editor APU.

