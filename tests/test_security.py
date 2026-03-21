"""Tests for core/security.py — TP-S01 through TP-S11."""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

from core.config import SECRET_KEY, ALGORITHM
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
)
from models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(token=None):
    """Build a mock Request with optional access_token cookie."""
    req = MagicMock()
    if token:
        req.cookies = {"access_token": f"Bearer {token}"}
    else:
        req.cookies = {}
    return req


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _create_active_user(db, email="user@test.com"):
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        is_active=True,
        deleted_at=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# TP-S01: create_access_token → valid JWT with sub and exp
# ---------------------------------------------------------------------------

def test_create_access_token_contains_sub_and_exp():
    token = create_access_token({"sub": "user@test.com"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user@test.com"
    assert "exp" in payload


# ---------------------------------------------------------------------------
# TP-S02: verify_password(correct) → True
# ---------------------------------------------------------------------------

def test_verify_password_correct():
    hashed = get_password_hash("secret")
    assert verify_password("secret", hashed) is True


# ---------------------------------------------------------------------------
# TP-S03: verify_password(wrong) → False
# ---------------------------------------------------------------------------

def test_verify_password_wrong():
    hashed = get_password_hash("secret")
    assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# TP-S04: get_password_hash → bcrypt hash ($2b$)
# ---------------------------------------------------------------------------

def test_get_password_hash_bcrypt():
    hashed = get_password_hash("mypassword")
    assert hashed.startswith("$2b$")


# ---------------------------------------------------------------------------
# TP-S05: get_current_user: no cookie → None
# ---------------------------------------------------------------------------

def test_get_current_user_no_cookie(db):
    req = make_request(token=None)
    result = run_async(get_current_user(req, db))
    assert result is None


# ---------------------------------------------------------------------------
# TP-S06: get_current_user: valid JWT → User
# ---------------------------------------------------------------------------

def test_get_current_user_valid_jwt(db):
    user = _create_active_user(db)
    token = create_access_token({"sub": user.email})
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is not None
    assert result.email == user.email


# ---------------------------------------------------------------------------
# TP-S07: get_current_user: expired JWT → None
# ---------------------------------------------------------------------------

def test_get_current_user_expired_jwt(db):
    _create_active_user(db)
    payload = {"sub": "user@test.com", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is None


# ---------------------------------------------------------------------------
# TP-S08: get_current_user: invalid signature → None
# ---------------------------------------------------------------------------

def test_get_current_user_invalid_signature(db):
    _create_active_user(db)
    token = jwt.encode({"sub": "user@test.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "wrong-secret", algorithm=ALGORITHM)
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is None


# ---------------------------------------------------------------------------
# TP-S09: get_current_user: JWT without "sub" → None
# ---------------------------------------------------------------------------

def test_get_current_user_no_sub(db):
    token = jwt.encode({"data": "nothing", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, SECRET_KEY, algorithm=ALGORITHM)
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is None


# ---------------------------------------------------------------------------
# TP-S10: get_current_user: deleted_at != None → None
# ---------------------------------------------------------------------------

def test_get_current_user_soft_deleted(db):
    user = User(
        email="deleted@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    token = create_access_token({"sub": "deleted@test.com"})
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is None


# ---------------------------------------------------------------------------
# TP-S11: get_current_user: is_active == False → None
# ---------------------------------------------------------------------------

def test_get_current_user_inactive(db):
    user = User(
        email="inactive@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        deleted_at=None,
    )
    db.add(user)
    db.commit()
    token = create_access_token({"sub": "inactive@test.com"})
    req = make_request(token=token)
    result = run_async(get_current_user(req, db))
    assert result is None
