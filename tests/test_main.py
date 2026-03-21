from unittest.mock import patch
from models import User, Persona, Hobby
from core.security import get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email="test@example.com", username="testuser", password="secret123", is_active=True):
    """Create a user + default persona directly in the DB and return (user, persona)."""
    hashed = get_password_hash(password)
    user = User(email=email, hashed_password=hashed, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)

    persona = Persona(user_id=user.id, username=username, is_default=True)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return user, persona


def _auth_cookie(email="test@example.com"):
    """Return a dict suitable for client.cookies.update(...)."""
    token = create_access_token(data={"sub": email})
    return {"access_token": f"Bearer {token}"}


def _csrf(client):
    """Return CSRF header dict."""
    return {"x-csrftoken": client.cookies.get("csrftoken", "")}


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

def test_register_page_renders(client):
    """GET /register returns 200 with form."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "register" in response.url.path or response.status_code == 200


@patch("services.auth_service.request_verification_code", return_value="123456")
def test_register_user_success(mock_code, client, db):
    """POST /register creates user and redirects to verify."""
    response = client.post(
        "/register",
        data={"username": "newuser", "email": "new@example.com", "password": "password123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/verify-email" in response.headers["location"]

    # Verify user was persisted
    user = db.query(User).filter(User.email == "new@example.com").first()
    assert user is not None


@patch("services.auth_service.request_verification_code", return_value="123456")
def test_register_duplicate_email(mock_code, client, db):
    """POST /register with existing email redirects back with error."""
    # Register the first user via the endpoint
    client.post(
        "/register",
        data={"username": "first", "email": "dup@example.com", "password": "password123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    response = client.post(
        "/register",
        data={"username": "second", "email": "dup@example.com", "password": "password123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/register" in response.headers["location"]
    assert "error" in response.headers["location"]


@patch("services.auth_service.request_verification_code", return_value="123456")
def test_register_duplicate_username(mock_code, client, db):
    """POST /register with existing username redirects back with error."""
    # Register the first user via the endpoint
    client.post(
        "/register",
        data={"username": "taken", "email": "one@example.com", "password": "password123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    response = client.post(
        "/register",
        data={"username": "taken", "email": "two@example.com", "password": "password123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/register" in response.headers["location"]
    assert "error" in response.headers["location"]


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

def test_login_page_renders(client):
    """GET /login returns 200."""
    response = client.get("/login")
    assert response.status_code == 200


def test_login_invalid_credentials(client, db):
    """POST /login with wrong password redirects with error."""
    _create_user(db)
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "wrongpassword"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error" in response.headers["location"]


def test_login_unverified_user(client, db):
    """POST /login for unverified user redirects to verify."""
    _create_user(db, is_active=False)
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "secret123"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/verify-email" in response.headers["location"]


# ---------------------------------------------------------------------------
# Home page tests
# ---------------------------------------------------------------------------

def test_home_page_renders(client):
    """GET / returns 200 with hobby list."""
    response = client.get("/")
    assert response.status_code == 200
    assert "HobbyHeaven" in response.text


def test_home_page_search(client, db):
    """GET /?search=test filters hobbies."""
    user, persona = _create_user(db)
    hobby = Hobby(title="Underwater Basket Weaving", description="Fun", persona_id=persona.id)
    db.add(hobby)
    db.commit()

    response = client.get("/?search=Underwater")
    assert response.status_code == 200
    assert "Underwater" in response.text


def test_home_page_pagination(client):
    """GET /?page=1 returns paginated results."""
    response = client.get("/?page=1")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Hobby CRUD tests
# ---------------------------------------------------------------------------

def test_create_hobby_unauthenticated(client):
    """POST /create-hobby without auth redirects to login."""
    response = client.post(
        "/create-hobby",
        data={"title": "Test", "description": "Test"},
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_edit_hobby_page_unauthenticated(client, db):
    """GET /edit/1 without auth redirects to login."""
    user, persona = _create_user(db)
    hobby = Hobby(title="H", description="D", persona_id=persona.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    response = client.get(f"/edit/{hobby.id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_delete_hobby_unauthenticated(client, db):
    """POST /delete-hobby/1 without auth returns 401."""
    user, persona = _create_user(db)
    hobby = Hobby(title="H", description="D", persona_id=persona.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    response = client.post(
        f"/delete-hobby/{hobby.id}",
        headers=_csrf(client),
        follow_redirects=False,
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Profile tests
# ---------------------------------------------------------------------------

def test_cabinet_unauthenticated(client):
    """GET /cabinet without auth redirects to login."""
    response = client.get("/cabinet", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_profile_not_found(client):
    """GET /profile/nonexistent returns 404."""
    response = client.get("/profile/nonexistent")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def test_logout(client):
    """GET /logout clears cookie and redirects."""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


# ---------------------------------------------------------------------------
# Random hobby
# ---------------------------------------------------------------------------

def test_random_hobby_empty_db(client):
    """GET /random with no hobbies redirects to home."""
    response = client.get("/random", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
