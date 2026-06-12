from __future__ import annotations

import pytest

from src.exceptions import RateLimitError
from src.utils import rate_limiter


@pytest.mark.asyncio
async def test_register_success(async_client):
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client):
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "user_already_exists"


@pytest.mark.asyncio
async def test_login_success(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "password123",
        },
    )
    assert registered.status_code == 201

    response = await async_client.post(
        "/api/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_me_success(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "me_test@example.com",
            "password": "password123",
        },
    )
    tokens = registered.json()

    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_test@example.com"
    assert data["is_verified"] is False


@pytest.mark.asyncio
async def test_refresh_with_valid_refresh_token_returns_token_pair(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "refresh_ok@example.com",
            "password": "password123",
        },
    )
    tokens = registered.json()

    response = await async_client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "refresh_wrong_type@example.com",
            "password": "password123",
        },
    )
    tokens = registered.json()

    response = await async_client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(async_client):
    response = await async_client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


@pytest.mark.asyncio
async def test_verify_email_request_and_consume(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "verify_test@example.com",
            "password": "password123",
        },
    )
    tokens = registered.json()

    request_response = await async_client.post(
        "/api/auth/verify-email/request",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert request_response.status_code == 200
    request_data = request_response.json()
    assert request_data["token"]
    assert request_data["action_url"]

    verify_response = await async_client.get(
        "/api/auth/verify-email",
        params={"token": request_data["token"]},
    )

    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["verified"] is True
    assert verify_data["email"] == "verify_test@example.com"


@pytest.mark.asyncio
async def test_forgot_password_and_reset_password(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "reset_test@example.com",
            "password": "password123",
        },
    )
    assert registered.status_code == 201

    forgot_response = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "reset_test@example.com"},
    )
    assert forgot_response.status_code == 200
    forgot_data = forgot_response.json()
    assert forgot_data["token"]
    assert forgot_data["action_url"]

    reset_response = await async_client.post(
        "/api/auth/reset-password",
        json={
            "token": forgot_data["token"],
            "new_password": "new-password123",
        },
    )
    assert reset_response.status_code == 200

    login_response = await async_client.post(
        "/api/auth/login",
        json={
            "email": "reset_test@example.com",
            "password": "new-password123",
        },
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(async_client):
    registered = await async_client.post(
        "/api/auth/register",
        json={
            "email": "logout_test@example.com",
            "password": "password123",
        },
    )
    tokens = registered.json()

    logout_response = await async_client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_response.status_code == 200

    refresh_response = await async_client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_breach_returns_clean_429(async_client, monkeypatch):
    async def _always_limit(_key: str, _limit: int) -> None:
        raise RateLimitError(retry_after=17, limit=10, window=60)

    monkeypatch.setattr(rate_limiter, "_hit_redis", _always_limit)

    response = await async_client.post(
        "/api/auth/login",
        json={
            "email": "any@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "17"
    body = response.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
    assert body["error"]["details"]["retry_after"] == 17
    assert body["error"]["details"]["limit"] == 10
    assert body["error"]["details"]["window"] == 60
