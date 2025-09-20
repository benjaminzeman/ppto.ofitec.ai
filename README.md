## OFITEC · Presupuestos, Mediciones, Versionado & Compras (MVP ampliado)

Monorepo con **frontend (Next.js 14)** y **backend (FastAPI)** implementando núcleo de:
- Presupuestos (Capítulos, Ítems, APU, Recursos)
- Importadores (Excel, BC3 simplificado)
- Mediciones (captura y resumen)
- Versionado (snapshots y diff)
- Compras / Comparativos inicial (RFQ, cotizaciones, ranking)
- Autenticación JWT básica

Basado en los documentos de arquitectura y sprints (v2 sin Odoo) con evolución incremental.

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

### Autenticación
Registro y login emiten un JWT (HS256). Incluir `Authorization: Bearer <token>` en endpoints protegidos de creación.

```
POST /api/v1/auth/register {"username":"u","password":"p"}
POST /api/v1/auth/login (form-urlencoded: username, password)
GET  /api/v1/auth/me
```

### Endpoints principales
Presupuestos:
- `GET /api/v1/budgets/projects`
- `POST /api/v1/budgets/projects` (auth)
- `POST /api/v1/budgets/chapters` (auth)
- `POST /api/v1/budgets/items` (auth)
- `POST /api/v1/budgets/items/{item_id}/apu` (auth)

Importación:
- `POST /api/v1/imports/excel` (auth) – Genera proyecto desde .xlsx
- `POST /api/v1/imports/bc3` (auth) – Parser BC3 simplificado

Mediciones:
- `POST /api/v1/measurements` (auth) – Registrar medición
- `GET /api/v1/measurements/{project_id}/summary` – Agregado por ítem

Versionado:
- `POST /api/v1/versions/{project_id}/snapshot?name=V1` (auth)
- `GET /api/v1/versions/diff?v_from=ID&v_to=ID`

Compras / Comparativos:
- `POST /api/v1/purchases/suppliers` (auth)
- `GET  /api/v1/purchases/suppliers` (auth)
- `POST /api/v1/purchases/rfq` (auth)
- `POST /api/v1/purchases/quote` (auth)
- `GET  /api/v1/purchases/rank/{rfq_id}` (auth) – Ranking por total

Health: `GET /health`

### Ejemplo rápido de import Excel (cURL)
```
TOKEN=$(curl -s -X POST http://localhost:5555/api/v1/auth/register -H 'Content-Type: application/json' -d '{"username":"demo","password":"demo"}' | jq -r .access_token)
curl -X POST http://localhost:5555/api/v1/imports/excel \
	-H "Authorization: Bearer $TOKEN" \
	-F project_name=Proyecto1 \
	-F file=@presupuesto.xlsx
```

### Import BC3 Formato Simplificado
Archivo `.bc3` con líneas tipo:
```
C;C1;Capítulo 1
I;C1;IT1;Item 1;m2;10
R;IT1;MAT;R1;Recurso 1;2;5
R;IT1;MO;R2;Mano Obra;0.5;40
```

### Tests
Se añadieron tests básicos (`pytest`) para: cálculo APU, import Excel, import BC3, snapshot/diff versiones.
```bash
docker compose build backend
docker compose run --rm backend pytest -q
```

### Roadmap (próximos sprints)
- Mediciones avanzadas: baseline, Curva S, CPI/SPI, ETC/EAC
- Exportaciones PDF/Excel (presupuesto, mediciones, versiones, diffs)
- Jobs background (Redis/RQ) para import y reportes pesados
- Roles / RBAC y permisos por proyecto
- CRUD completo (updates/deletes) y endpoints de lectura agregada avanzada
- Observabilidad: métricas Prometheus, logging estructurado, tracing
- Frontend: vistas completas (mediciones, versiones, diff, compras)
- Parser BC3 extendido (más campos FIEBDC-3)

### Variables de entorno clave (.env)
```
DATABASE_URL=postgresql+psycopg2://ofitec:ofitec@db:5432/ofitec
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change_me
ALLOWED_ORIGINS=http://localhost:3001
NEXT_PUBLIC_API_BASE=http://localhost:5555
```

### Consideraciones de Seguridad
- Usar un `JWT_SECRET` robusto en producción.
- Añadir expiración corta + refresh tokens (pendiente).
- Implementar roles y control de acceso por proyecto (pendiente).

### Estado Actual
MVP enriquecido operativo con: auth, importadores, mediciones básicas, versiones (diff), módulo compras inicial y tests básicos.

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

