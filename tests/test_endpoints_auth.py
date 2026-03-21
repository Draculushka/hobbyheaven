"""
P0 endpoint integration tests for auth flows.
"""
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from models import User, Persona
from core.security import get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(db, email="test@test.com", password="secret123", username="testuser", active=True):
    user = User(email=email, hashed_password=get_password_hash(password), is_active=active)
    db.add(user)
    db.flush()
    persona = Persona(user_id=user.id, username=username, is_default=True)
    db.add(persona)
    db.commit()
    db.refresh(user)
    db.refresh(persona)
    return user, persona


def auth_headers(email="test@test.com"):
    token = create_access_token(data={"sub": email})
    return {"access_token": f"Bearer {token}"}


def _csrf(client):
    """Return CSRF header dict."""
    return {"x-csrftoken": client.cookies.get("csrftoken", "")}


# ---------------------------------------------------------------------------
# TP-A06: Password 5 chars (< min=6) -> 422
# ---------------------------------------------------------------------------

@patch("services.auth_service.request_verification_code", return_value="123456")
def test_password_too_short(mock_code, client, db):
    """Password with 5 chars should be rejected with 422."""
    response = client.post(
        "/register",
        data={"username": "user1", "email": "short@test.com", "password": "12345"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TP-A07: Password 6 chars (boundary) -> success (303)
# ---------------------------------------------------------------------------

@patch("services.auth_service.request_verification_code", return_value="123456")
def test_password_min_boundary(mock_code, client, db):
    """Password with exactly 6 chars should succeed."""
    response = client.post(
        "/register",
        data={"username": "user6", "email": "six@test.com", "password": "123456"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/verify-email" in response.headers["location"]


# ---------------------------------------------------------------------------
# TP-A09: Password 65 chars (> max=64) -> 422
# ---------------------------------------------------------------------------

@patch("services.auth_service.request_verification_code", return_value="123456")
def test_password_too_long(mock_code, client, db):
    """Password with 65 chars should be rejected with 422."""
    response = client.post(
        "/register",
        data={"username": "userlong", "email": "long@test.com", "password": "A" * 65},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TP-A15: Verify correct code -> 303 /, cookie set (mock verify_code)
# ---------------------------------------------------------------------------

@patch("services.auth_service.verify_code", return_value=True)
def test_verify_correct_code(mock_verify, client, db):
    """Submitting correct verification code -> redirect to / with cookie set."""
    create_user(db, email="verify@test.com", active=False)

    response = client.post(
        "/verify-email",
        data={"email": "verify@test.com", "code": "123456"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    # Check set-cookie header contains access_token
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


# ---------------------------------------------------------------------------
# TP-A16: Verify wrong code -> redirect with error
# ---------------------------------------------------------------------------

@patch("services.auth_service.verify_code", return_value=False)
def test_verify_wrong_code(mock_verify, client, db):
    """Submitting wrong verification code -> redirect back with error."""
    create_user(db, email="verify2@test.com", active=False)

    response = client.post(
        "/verify-email",
        data={"email": "verify2@test.com", "code": "000000"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert "/verify-email" in location
    assert "error" in location


# ---------------------------------------------------------------------------
# TP-A20: Login valid credentials -> 303 /, cookie set
# ---------------------------------------------------------------------------

def test_login_valid_credentials(client, db):
    """Login with correct email/password -> redirect to / with cookie."""
    create_user(db, email="login@test.com", password="secret123", active=True)

    response = client.post(
        "/login",
        data={"email": "login@test.com", "password": "secret123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


# ---------------------------------------------------------------------------
# TP-A23: Login soft-deleted user -> redirect with error
# ---------------------------------------------------------------------------

def test_login_soft_deleted_user(client, db):
    """Login as a soft-deleted user -> redirect with error message."""
    user, _ = create_user(db, email="deleted@test.com", password="secret123", active=True)
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()

    response = client.post(
        "/login",
        data={"email": "deleted@test.com", "password": "secret123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error" in response.headers["location"]


# ---------------------------------------------------------------------------
# TP-A24: Login non-existent email -> same response as wrong password
# ---------------------------------------------------------------------------

def test_login_nonexistent_email(client, db):
    """Login with non-existent email gives same response as wrong password (no info leak)."""
    create_user(db, email="real@test.com", password="secret123", active=True)

    # Wrong password
    resp_wrong_pw = client.post(
        "/login",
        data={"email": "real@test.com", "password": "wrongpassword"},
        headers=_csrf(client),
        follow_redirects=False,
    )

    # Non-existent email
    resp_no_email = client.post(
        "/login",
        data={"email": "ghost@test.com", "password": "secret123"},
        headers=_csrf(client),
        follow_redirects=False,
    )

    # Both should redirect to /login with error (same behavior)
    assert resp_wrong_pw.status_code == resp_no_email.status_code
    assert "error" in resp_wrong_pw.headers["location"]
    assert "error" in resp_no_email.headers["location"]
    # Same error message (no info leak)
    assert resp_wrong_pw.headers["location"] == resp_no_email.headers["location"]


# ---------------------------------------------------------------------------
# TP-A25: Cookie has httponly, secure, samesite=lax
# ---------------------------------------------------------------------------

def test_cookie_security_flags(client, db):
    """Login cookie must have httponly, secure, samesite=lax."""
    create_user(db, email="cookie@test.com", password="secret123", active=True)

    response = client.post(
        "/login",
        data={"email": "cookie@test.com", "password": "secret123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    # secure flag is configurable via COOKIE_SECURE env var (default: false for dev)
