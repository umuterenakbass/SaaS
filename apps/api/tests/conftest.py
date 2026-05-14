from collections.abc import Generator

import app.models.announcement  # noqa: F401
import app.models.block  # noqa: F401
import app.models.charge  # noqa: F401
import app.models.charge_plan  # noqa: F401
import app.models.flat  # noqa: F401
import app.models.maintenance_request  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.payment  # noqa: F401
import app.models.payment_allocation  # noqa: F401
import app.models.resident_flat_relation  # noqa: F401
import app.models.scheduled_charge  # noqa: F401
import app.models.site  # noqa: F401
import app.models.user  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
