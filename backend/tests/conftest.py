import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"  # override simple

from app.main import app
from app.db.base import Base
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
    # registrar usuario
    r = client.post("/api/v1/auth/register", json={"username": "tester", "password": "pass"})
    return r.json()["access_token"]
