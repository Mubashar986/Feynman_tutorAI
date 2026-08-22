import pytest
from httpx import AsyncClient

from backend.app.auth.models import UserRole
from backend.app.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ==============================================================================
# 1. Cryptographic Security Unit Tests
# ==============================================================================

def test_password_hash_and_verify():
    raw_pass = "SuperSecret123!"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert hashed.startswith("$2b$")  # bcrypt prefix
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_create_and_decode():
    user_id = "test-user-uuid-1234"
    role = "student"
    token = create_access_token(user_id=user_id, role=role)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_token(token)
    assert payload is not None
    assert payload.sub == user_id
    assert payload.role == role
    assert payload.exp > 0


def test_jwt_decode_invalid_token():
    assert decode_token("invalid.token.string") is None


# ==============================================================================
# 2. Authentication Endpoint Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    payload = {
        "email": "alex.student@example.com",
        "password": "SecurePassword123!",
        "full_name": "Alex Rivera",
        "role": "student",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alex.student@example.com"
    assert data["full_name"] == "Alex Rivera"
    assert data["role"] == "student"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(async_client: AsyncClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "full_name": "Original User",
        "role": "student",
    }
    resp1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Attempt second registration with same email
    resp2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    # Register first
    reg_payload = {
        "email": "login.test@example.com",
        "password": "MySecretPassword123!",
        "full_name": "Login Tester",
        "role": "student",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login.test@example.com",
        "password": "MySecretPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login.test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    reg_payload = {
        "email": "wrong.pass@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Pass Tester",
        "role": "student",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Login with wrong password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "wrong.pass@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_me(async_client: AsyncClient):
    # Register & Login
    email = "get.me@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Me User", "role": "student"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]

    # Call /me with Bearer token
    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    # No auth header
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    # Invalid token
    resp_bad = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake.jwt.token"},
    )
    assert resp_bad.status_code == 401


# ==============================================================================
# 3. Server-Side Role-Based Access Control (RBAC) Tests (PRD Constraint #6)
# ==============================================================================

@pytest.mark.asyncio
async def test_rbac_instructor_access_granted(async_client: AsyncClient):
    # Register Instructor
    email = "prof.einstein@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Prof Einstein", "role": "instructor"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]

    # Access instructor-only route
    resp = await async_client.get(
        "/api/v1/auth/instructor-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "instructor"


@pytest.mark.asyncio
async def test_rbac_student_access_forbidden(async_client: AsyncClient):
    # Register Student
    email = "regular.student@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Student Bob", "role": "student"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]

    # Attempt to access instructor-only route -> MUST BE 403 FORBIDDEN
    resp = await async_client.get(
        "/api/v1/auth/instructor-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "Access forbidden" in resp.json()["detail"]
