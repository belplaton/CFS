"""
Tests for Auth Service endpoints
"""
import pytest
from httpx import ASGITransport, Client

from src.main import app
from src.models import Base, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool


# Setup in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine):
    async with async_sessionmaker(test_engine, class_=AsyncSession) as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(test_engine):
    transport = ASGITransport(app)
    async with Client(transport=transport, base_url="http://test") as client:
        yield client


# ==================== Registration Tests ====================

@pytest.mark.asyncio
async def test_register_success(async_client, db_session):
    """Test successful user registration"""
    response = await async_client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client, db_session):
    """Test registration with existing email"""
    # First registration
    await async_client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password123",
    })

    # Second registration with same email
    response = await async_client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password456",
    })

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_email_case_insensitive(async_client, db_session):
    """Test that registration normalizes email (lowercase)"""
    response = await async_client.post("/api/auth/register", json={
        "email": "CaseSensitive@Example.COM",
        "password": "password123",
    })

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data


# ==================== Login Tests ====================

@pytest.mark.asyncio
async def test_login_success(async_client, db_session):
    """Test successful login"""
    # Register first
    reg_response = await async_client.post("/api/auth/register", json={
        "email": "login_test@example.com",
        "password": "password123",
    })
    assert reg_response.status_code == 201

    # Login
    response = await async_client.post("/api/auth/login", json={
        "email": "login_test@example.com",
        "password": "password123",
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(async_client, db_session):
    """Test login with wrong password"""
    # Register first
    await async_client.post("/api/auth/register", json={
        "email": "wrong_pass@example.com",
        "password": "password123",
    })

    # Try login with wrong password
    response = await async_client.post("/api/auth/login", json={
        "email": "wrong_pass@example.com",
        "password": "wrongpassword",
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email(async_client, db_session):
    """Test login with non-existent email"""
    response = await async_client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123",
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


# ==================== Get Me Tests ====================

@pytest.mark.asyncio
async def test_get_me_success(async_client, db_session):
    """Test getting current user info with valid token"""
    # Register
    reg_response = await async_client.post("/api/auth/register", json={
        "email": "me_test@example.com",
        "password": "password123",
    })
    tokens = reg_response.json()
    access_token = tokens["access_token"]

    # Get me
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_test@example.com"
    assert data["is_verified"] is True
    assert "full_name" in data


@pytest.mark.asyncio
async def test_get_me_no_token(async_client, db_session):
    """Test getting current user info without token"""
    response = await async_client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(async_client, db_session):
    """Test getting current user info with invalid token"""
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
