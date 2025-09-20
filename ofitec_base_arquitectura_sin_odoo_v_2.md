# OFITEC · Base Arquitectura (sin Odoo) – v2

> **Propósito**: Reemplazar completamente cualquier mención o dependencia de Odoo. Esta versión consolida la arquitectura **independiente** basada en **Next.js + Flask + SQLite/Docker**, alineada con los sprints ya definidos.

---

## 1) Principios de diseño
- **Independencia**: cero acoplamiento a ERPs externos. Integraciones solo vía conectores (API) opcionales.
- **Monorepo**: frontend, backend, servicios y docs en un único repositorio.
- **12-Factor App**: configuración por variables de entorno, logs estructurados, build reproducible.
- **API-first**: contratos REST/JSON estables, versionados (`/api/v1/...`).
- **Escalabilidad gradual**: SQLite → Postgres cuando sea necesario; Docker para portabilidad.
- **Observabilidad**: auditoría de eventos de dominio y trazas de API.

---

## 2) Stack tecnológico
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui.
- **Backend**: Python Flask (FastAPI-like patterns), SQLAlchemy, Alembic.
- **DB**: SQLite (`/data/ofitec.db`) en dev; Postgres en prod (opcional).
- **Infra**: Docker + Devcontainer; Makefile para tareas.
- **AI Bridge** (opcional): capa para ML/LLM y simulaciones.

---

## 3) Estructura de carpetas (monorepo)
```
ofitec.ai/
├─ frontend/                  # Next.js 14
│  ├─ app/
│  ├─ components/
│  └─ lib/
├─ backend/                   # Flask
│  ├─ app/
│  │  ├─ api/v1/             # Blueprints/routers
│  │  ├─ services/           # Lógica de dominio
│  │  ├─ db/models/          # SQLAlchemy models
│  │  ├─ db/session.py
│  │  └─ core/               # config, security, utils
│  └─ alembic/versions/      # migraciones
├─ services/
│  └─ ai_bridge/             # ML, simulaciones, predicciones
├─ docs/                      # especificaciones, sprints
├─ scripts/                   # herramientas CLI/CI
├─ .devcontainer/
├─ docker-compose.yml
├─ Makefile
└─ .env.example
```

---

## 4) Modelo de datos base (resumen)
- **projects**: obras/proyectos con metadatos básicos.
- **budget_versions, items**: versiones de presupuesto y partidas.
- **measurements, certifications**: mediciones y estados de pago.
- **invoices, bank_transactions**: facturación y conciliación bancaria.
- **cash_scenarios**: escenarios de flujo de caja.
- **documents, signatures**: documentos y firma digital.
- **risks, audit_logs**: riesgos y auditoría.
> Las tablas fueron introducidas progresivamente en los sprints 1–18 y extendidas en sprints posteriores (factoring, dashboards, tributario, IFRS, multi-país/moneda, BI, IA, etc.).

---

## 5) API (contratos REST)
- **Base**: `/api/v1/` con Blueprints separados por dominio.
- **Ejemplos**:
  - `POST /api/v1/budgets/create` (crear versión de presupuesto)
  - `POST /api/v1/certifications/create` (certificar por periodo)
  - `GET  /api/v1/cash/{projectId}/simulate` (simulación de caja)
  - `POST /api/v1/invoices/create` y `/send/{invoice_id}` (SII sandbox)
  - `POST /api/v1/bank/import` y `GET /{project_id}/reconcile` (cartolas + match)
  - `GET  /api/v1/dashboards/global` (KPIs globales)
  - `POST /api/v1/reports/excel|pdf` (exportables)
  - Módulos avanzados: `tax_ai`, `ifrs`, `forecast`, `fx`, `bi_*`, `workflows_*`.

**Autenticación** (opcional): JWT con `Authorization: Bearer <token>`.

---

## 6) Frontend (Next.js)
- Páginas principales: `/(projects|budgets|measurements|certifications|invoices|bank|cash|documents|dashboards|reports)`
- Componentes core: tablas (DataTable), formularios (react-hook-form), gráficos (recharts), upload/preview PDF.
- Diseño: Tailwind + shadcn/ui, dark mode opcional.

---

## 7) Dev & Deploy
**Variables de entorno (`.env`)**
```
FLASK_ENV=development
DATABASE_URL=sqlite:///data/ofitec.db
SII_USER=...
SII_PASS=...
FX_API=...
SIGN_API=...
```

**Docker Compose (dev)**
- `frontend`: `node:18`, puerto `3001`.
- `backend`: `python:3.11`, puerto `5555`, volumen `data/`.

**Migrations**
```bash
make db-upgrade   # alembic upgrade head
make db-revision  # alembic revision -m "desc"
```

**CI/CD (sugerido)**
- Lint/format: `ruff`, `black`, `eslint`.
- Tests: `pytest` (backend), `vitest` (frontend).
- Build: Docker multi-stage; despliegue en Render/Fly/EC2.

---

## 8) Integraciones (opcionales, vía API)
- **SII (DTE sandbox)** para facturación.
- **Fintoc** para cartolas bancarias.
- **Firmas** (firma avanzada): proveedor externo por API.
- **BI externo**: export CSV/JSON para PowerBI/Tableau.
> *Todas como conectores desacoplados. Sin Odoo.*

---

## 9) Plan de transición (remover Odoo por completo)
1. **Eliminar referencias**: borrar cualquier mención a Odoo en `README`, docs y comentarios.
2. **Asegurar independencia**: validar que ningún endpoint/servicio consuma modelos o endpoints de Odoo.
3. **Revisar migraciones**: confirmar que las tablas no tengan trazas de nomenclatura Odoo.
4. **Integraciones**: mantener solo conectores REST externos (SII, bancos, firma, BI).
5. **Check QA**: correr tests de dominio (presupuestos, mediciones, certificaciones, facturas, conciliación).

**Checklist**
- [ ] No quedan strings “odoo” en el repo.
- [ ] README actualizado al stack Next.js + Flask.
- [ ] Pip/Node deps sin módulos Odoo.
- [ ] Pipelines CI/CD verdes.

---

## 10) Mapa de Sprints ↔ Arquitectura
- **S1–S6**: Presupuesto & Mediciones base (Next.js + Flask + SQLite).
- **S7–S10**: Aprobaciones, Riesgos, Certificaciones, Caja, Documentos.
- **S11–S16**: DTE SII, Conciliación, Reportes, IA Factoring, Forecast.
- **S17–S24**: Contabilidad, Firma digital, Multi-empresa, IFRS, escenarios.
- **S25–S34**: Multi-país/moneda, BI embebido, ML FX, combinaciones IFRS/tributos.
- **S35–S46**: Recomendador IA, workflows, Montecarlo, KPIs predictivos.
- **S47+**: Consolidación y optimizaciones (no dependientes de ERPs).

---

## 11) Ejemplo mínimo ejecutable (dev)
**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///../data/ofitec.db
alembic upgrade head
flask --app app.main:app run -p 5555 --reload
```

**Frontend**
```bash
cd frontend
pnpm install
pnpm dev --port 3001
```

---

## 12) Futuro inmediato
- Switch SQLite→Postgres (si >1 usuario concurrente real).
- Autenticación y RBAC en backend (JWT + roles).
- Telemetría unificada (logs, métricas, traces) con OpenTelemetry.
- Tests E2E (Playwright) para flujos críticos.

---

### Nota
Esta **v2 sin Odoo** sustituye al documento base anterior. Puedes incluirla en `docs/arquitectura/ofitec_base_sin_odoo.md` y referenciarla desde el README principal.

