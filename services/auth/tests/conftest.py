"""
Pytest configuration and fixtures for Auth Service
"""
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, Client

from src.main import app
from src.models import Base, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool


# Use a separate in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test engine with SQLite"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db(test_engine):
    """Create tables for test session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine):
    """Create a fresh session for each test"""
    async with async_sessionmaker(test_engine, class_=AsyncSession) as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    # Override the database dependency if needed, or use the test engine
    # For simplicity, we'll use the app's default DB for now, but in real tests, you'd override get_db
    with TestClient(app) as client:
        yield client


# Note: For full async testing, you might want to use httpx.AsyncClient with ASGITransport
# Example:
# @pytest.fixture
# async def async_client():
#     transport = ASGITransport(app=app)
#     async with Client(transport=transport, base_url="http://test") as client:
#         yield client
