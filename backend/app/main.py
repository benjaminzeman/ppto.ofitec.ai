from fastapi import FastAPI, Response
from contextlib import asynccontextmanager
from sqlalchemy import text
import redis
from alembic import command
from alembic.config import Config
import os
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import engine
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import budgets, measurements, imports, purchases, auth, versions, evm, exports, jobs, workflows, risks, dashboard, invoices
from app.core.settings import get_settings
from app.core.logging_middleware import LoggingMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ejecutar migraciones
    if not settings.skip_migrations:
        alembic_dir = os.path.join(os.path.dirname(__file__), "..", "alembic")
        if os.path.isdir(os.path.abspath(alembic_dir)):
            cfg = Config(os.path.abspath(os.path.join(alembic_dir, "..", "alembic.ini")))
            cfg.set_main_option("sqlalchemy.url", settings.database_url)
            try:
                command.upgrade(cfg, "head")
            except Exception as e:
                print(f"[alembic] migraciones fallaron: {e}")
    else:
        print("[startup] SKIP_MIGRATIONS=True -> no se ejecutan migraciones")
    yield
    # Shutdown: (placeholder para futuras tareas de cierre limpio)

app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

# -------- Prometheus metrics --------
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'path', 'status']
)
REQUEST_LATENCY = Histogram(
    'app_request_duration_seconds',
    'Request latency seconds',
    ['method', 'path']
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    path = request.url.path
    # Opcional: agrupar rutas dinámicas simples
    if path.startswith('/api/v1/budgets/chapters/'):
        path_label = '/api/v1/budgets/chapters/:id'
    elif path.startswith('/api/v1/budgets/items/'):
        path_label = '/api/v1/budgets/items/:id'
    else:
        path_label = path
    REQUEST_COUNT.labels(request.method, path_label, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path_label).observe(elapsed)
    return response

@app.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["budgets"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["measurements"])
app.include_router(imports.router, prefix="/api/v1/imports", tags=["imports"])
app.include_router(purchases.router, prefix="/api/v1/purchases", tags=["purchases"])
app.include_router(versions.router, prefix="/api/v1/versions", tags=["versions"])
app.include_router(evm.router, prefix="/api/v1/evm", tags=["evm"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["exports"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(risks.router, prefix="/api/v1/risks", tags=["risks"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(invoices.router, prefix="/api/v1", tags=["invoices"])


@app.get("/health")
async def health():
    status = {"status": "ok", "environment": settings.environment}
    # DB check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = "up"
    except SQLAlchemyError as e:
        status["database"] = f"down: {e}"; status["status"] = "degraded"
    # Redis check
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        r.ping()
        status["redis"] = "up"
    except Exception as e:
        status["redis"] = f"down: {e}"; status["status"] = "degraded"
    return status
