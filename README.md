## OFITEC · Presupuestos & Mediciones (MVP)

Monorepo que contiene el **frontend (Next.js 14)** y el **backend (FastAPI)** para el núcleo de Presupuestos / Mediciones / APU. Basado en los documentos de arquitectura v2 sin Odoo.

### Estructura
```
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   ├── db/
│   │   └── services/
├── frontend/
│   └── app/
├── scripts/
│   └── seed_demo.py
├── docker-compose.yml
├── .env.example
└── docs/
```

### Requisitos
- Docker + Docker Compose

### Puertos
- Backend: `5555`
- Frontend: `3001`
- Postgres: `5432`
- Redis: `6379`

### Primer uso
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_demo.py
```

Abrir: http://localhost:3001
Healthcheck API: http://localhost:5555/health

### Endpoints iniciales
- `GET /api/v1/budgets/projects`
- `POST /api/v1/budgets/projects`
- `POST /api/v1/budgets/chapters`
- `POST /api/v1/budgets/items`
- `POST /api/v1/budgets/items/{item_id}/apu`
- `POST /api/v1/imports/excel` (stub)

### Próximos pasos
- Implementar importadores Excel / BC3 reales.
- Añadir Measurements summary y comparativos.
- Versionado de presupuestos y snapshots.
- Seguridad (JWT + roles) y auditoría.

### Desarrollo local sin Docker (opcional)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///dev.db
alembic upgrade head
uvicorn app.main:app --reload --port 5555
```
```bash
cd frontend
npm install
npm run dev -- -p 3001
```

### Licencia
Pendiente.

