import os
import sys
from pathlib import Path
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Asegurar que 'backend' esté en PYTHONPATH para que 'app' sea importable
ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Forzar uso de sqlite aislado y saltar migraciones en tests
os.environ["DATABASE_URL"] = "sqlite:///./test.db"  # override simple
os.environ["SKIP_MIGRATIONS"] = "true"

from app.main import app
from app.db.base import Base
# Importar todos los modelos necesarios antes de create_all para asegurar creación de tablas
from app.db.models import user as _m_user  # noqa: F401
from app.db.models import project as _m_project  # noqa: F401
from app.db.models import budget as _m_budget  # noqa: F401
from app.db.models import versioning as _m_versioning  # noqa: F401
from app.db.models import audit as _m_audit  # noqa: F401
from app.db.models import risk as _m_risk  # noqa: F401
from app.db.session import get_db


@pytest.fixture(scope="session")
def engine():
    fd, path = tempfile.mkstemp(prefix="testdb", suffix=".sqlite")
    url = f"sqlite:///{path}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    import uuid
    username = f"tester_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/auth/register", json={"username": username, "password": "pass"})
    if r.status_code != 200:
        raise AssertionError(f"Fallo al registrar usuario de test: {r.status_code} {r.text}")
    return r.json()["access_token"]
