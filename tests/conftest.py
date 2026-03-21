import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import get_db
from models import Base
from main import app

# Truly in-memory SQLite database with StaticPool so all connections share the same DB
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # Trigger CSRF cookie by doing a GET request
        c.get("/login")
        yield c
    app.dependency_overrides.clear()


def csrf_form_data(client, data=None):
    """Add CSRF token to form data for POST requests."""
    csrf = client.cookies.get("csrftoken", "")
    result = {"csrftoken": csrf}
    if data:
        result.update(data)
    return result


def csrf_headers(client):
    """Return headers dict with CSRF token for POST requests."""
    csrf = client.cookies.get("csrftoken", "")
    return {"x-csrftoken": csrf}
