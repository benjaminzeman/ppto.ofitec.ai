# Entorno de Desarrollo (Dev Container / Docker Compose)

## Objetivo
Entorno reproducible para backend (FastAPI) y frontend (Next.js) con Postgres y Redis.

## Servicios
- db: Postgres 15
- redis: Redis 7
- backend: FastAPI (uvicorn) puerto interno 5555
- frontend: Next.js puerto interno 3000 (expuesto como 3001 en host)

## Cambios Clave Implementados
1. Archivo `.env` agregado con variables base (DB, Redis, puertos).
2. Volumen adicional `/app/node_modules` para que `node_modules` no se pierda al montar el código del host en frontend.
3. Limpieza de `postCreateCommand` en `devcontainer.json` (solo instala dependencias Python, no intenta `npm install` en el contenedor equivocado).
4. Script `app/wait_for_db.py` que espera a Postgres antes de levantar uvicorn.
5. Ajuste de `forwardPorts` a `[3000, 5555]`.
 6. Configuración centralizada `app/core/settings.py` con Pydantic y lectura de `.env`.
 7. Endpoint `/health` ampliado: verifica base de datos y Redis (estado `degraded` si falla alguno).
 8. Migraciones Alembic se ejecutan automáticamente en `startup` (`upgrade head`).
 9. Middleware de logging estructurado JSON por request (`app/core/logging_middleware.py`).
 10. Usuario no-root en imagen backend (`appuser`).
 11. Healthchecks añadidos en `docker-compose.yml` para Postgres, Redis y Backend.
 12. Flag `SKIP_MIGRATIONS` para desactivar migraciones (tests / entornos efímeros).
 13. Tests básicos (`tests/test_health.py`, `tests/test_auth_basic.py`).
 14. Workflow CI GitHub Actions (`.github/workflows/ci.yml`).

## Primer Uso (Local fuera de devcontainer)
Asegúrate de tener Docker instalado. Luego:
```bash
docker compose build
docker compose up -d
```
Backend: http://localhost:5555/docs  
Frontend: http://localhost:3001
Health: http://localhost:5555/health

## Uso dentro de VS Code (Dev Container)
1. Ejecuta "Reopen in Container".
2. Al finalizar la creación:
   - Python deps ya instaladas vía `postCreateCommand`.
   - Para el frontend, las dependencias se instalan en la fase de build de la imagen y persisten gracias al volumen `/app/node_modules`.

Si modificas `package.json`:
```bash
docker compose exec frontend npm install
```

Si modificas `requirements.txt` (backend):
```bash
docker compose exec backend pip install -r requirements.txt
```

## Regenerar desde cero
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Logs
```bash
docker compose logs -f backend
# o
docker compose logs -f frontend
```

## Variables Clave
- `DATABASE_URL` para SQLAlchemy.
- `REDIS_URL` para tareas/colas futuras.
- `JWT_SECRET` para firmar tokens.
- `SKIP_MIGRATIONS` (true/false) para saltar migraciones en tests o pipelines rápidos.

## Notas
- Si Docker no está disponible en el entorno actual (por ejemplo en CI restringido), los comandos pueden fallar. Verifica instalación de Docker.
- Puede añadirse healthcheck y usuario no root en futuras mejoras.

## Próximos Mejorables (Opcional)
 - Añadir lint/format CI (ruff/black/isort).
 - Integrar coverage report y badge.
 - Añadir caching pip/node en CI para acelerar builds.
 - Implementar rate limiting / throttling en auth.
 - Métricas Prometheus (latencia, errores) y tracing.
