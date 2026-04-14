import os

# Must be set before importing app (engine binds at import time).
os.environ["APP_MODE"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["USE_MOCK_XAI"] = "true"
os.environ["XAI_ENABLE_REAL_CALLS"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base


@pytest.fixture
def db_session():
    # StaticPool: single shared :memory: DB across connections (create_all + Session)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
