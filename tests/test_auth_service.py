import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from models import User, Persona
from core.security import verify_password
from services.auth_service import (
    create_user,
    authenticate_user,
    request_verification_code,
    verify_code,
)


# ── create_user ──────────────────────────────────────────────────────────────

class TestCreateUser:
    def test_tp_as01_creates_user_and_default_persona(self, db):
        """TP-AS01: Valid data creates User + default Persona (is_default=True)."""
        user = create_user(db, username="alice", email="alice@test.com", password="secret123")

        assert user is not None
        assert user.email == "alice@test.com"

        personas = db.query(Persona).filter(Persona.user_id == user.id).all()
        assert len(personas) == 1
        assert personas[0].username == "alice"
        assert personas[0].is_default is True

    def test_tp_as03_new_user_is_inactive(self, db):
        """TP-AS03: New User.is_active == False by default."""
        user = create_user(db, username="bob", email="bob@test.com", password="secret123")
        assert user.is_active is False

    def test_tp_as04_password_is_hashed(self, db):
        """TP-AS04: Password is hashed (hashed_password != plain password)."""
        plain = "secret123"
        user = create_user(db, username="carol", email="carol@test.com", password=plain)

        assert user.hashed_password != plain
        assert verify_password(plain, user.hashed_password) is True

    def test_tp_as05_flush_gives_user_id_before_commit(self, db):
        """TP-AS05: flush() gives user.id so Persona.user_id is correctly set."""
        user = create_user(db, username="dave", email="dave@test.com", password="secret123")

        persona = db.query(Persona).filter(Persona.user_id == user.id).first()
        assert user.id is not None
        assert persona is not None
        assert persona.user_id == user.id


# ── authenticate_user ────────────────────────────────────────────────────────

class TestAuthenticateUser:
    def _make_user(self, db, email="user@test.com", password="correct", **kwargs):
        from core.security import get_password_hash
        user = User(email=email, hashed_password=get_password_hash(password), **kwargs)
        db.add(user)
        db.commit()
        return user

    def test_tp_as06_correct_credentials(self, db):
        """TP-AS06: Correct email + password returns User."""
        self._make_user(db)
        result = authenticate_user(db, "user@test.com", "correct")
        assert result is not None
        assert result.email == "user@test.com"

    def test_tp_as07_wrong_password(self, db):
        """TP-AS07: Correct email + wrong password returns None."""
        self._make_user(db)
        result = authenticate_user(db, "user@test.com", "wrong")
        assert result is None

    def test_tp_as08_nonexistent_email(self, db):
        """TP-AS08: Non-existent email returns None."""
        result = authenticate_user(db, "ghost@test.com", "any")
        assert result is None

    def test_tp_as09_soft_deleted_user(self, db):
        """TP-AS09: Soft-deleted user (deleted_at != None) returns None."""
        self._make_user(db, deleted_at=datetime.now(timezone.utc))
        result = authenticate_user(db, "user@test.com", "correct")
        assert result is None


# ── request_verification_code ────────────────────────────────────────────────

class TestRequestVerificationCode:
    @patch("services.auth_service.redis_client")
    def test_tp_as10_first_request_returns_code_and_sets_redis(self, mock_redis):
        """TP-AS10: First request returns 6-digit code, setex called with TTL 600."""
        mock_redis.exists.return_value = False

        code = request_verification_code("test@test.com")

        assert code is not None
        assert len(code) == 6
        assert 100000 <= int(code) <= 999999
        mock_redis.setex.assert_any_call("code_test@test.com", 600, code)
        mock_redis.setex.assert_any_call("cooldown_test@test.com", 60, "1")

    @patch("services.auth_service.redis_client")
    def test_tp_as11_request_during_cooldown_returns_none(self, mock_redis):
        """TP-AS11: Request during cooldown returns None."""
        mock_redis.exists.return_value = True

        result = request_verification_code("test@test.com")
        assert result is None

    @patch("services.auth_service.redis_client")
    def test_tp_as12_code_range(self, mock_redis):
        """TP-AS12: Code is always 100000-999999."""
        mock_redis.exists.return_value = False

        for _ in range(50):
            code = request_verification_code("range@test.com")
            assert code is not None
            assert 100000 <= int(code) <= 999999


# ── verify_code ──────────────────────────────────────────────────────────────

class TestVerifyCode:
    def _make_user(self, db, email="v@test.com"):
        from core.security import get_password_hash
        user = User(email=email, hashed_password=get_password_hash("pw"))
        db.add(user)
        db.commit()
        return user

    @patch("services.auth_service.redis_client")
    def test_tp_as14_correct_code_activates_user(self, mock_redis, db):
        """TP-AS14: Correct code sets is_active=True, deletes keys, returns True."""
        user = self._make_user(db)
        assert user.is_active is False

        mock_redis.get.side_effect = lambda key: {
            "attempts_v@test.com": None,
            "code_v@test.com": "123456",
        }.get(key)

        result = verify_code(db, "v@test.com", "123456")

        assert result is True
        db.refresh(user)
        assert user.is_active is True
        mock_redis.delete.assert_any_call("code_v@test.com")
        mock_redis.delete.assert_any_call("attempts_v@test.com")

    @patch("services.auth_service.redis_client")
    def test_tp_as15_wrong_code_increments_attempts(self, mock_redis, db):
        """TP-AS15: Wrong code increments attempts, returns False."""
        self._make_user(db)

        mock_redis.get.side_effect = lambda key: {
            "attempts_v@test.com": None,
            "code_v@test.com": "123456",
        }.get(key)

        result = verify_code(db, "v@test.com", "000000")

        assert result is False
        mock_redis.incr.assert_called_once_with("attempts_v@test.com")
        mock_redis.expire.assert_called_once_with("attempts_v@test.com", 600)

    @patch("services.auth_service.redis_client")
    def test_tp_as16_fifth_attempt_blocks_and_deletes_keys(self, mock_redis, db):
        """TP-AS16: 5th attempt blocks, deletes keys, returns False."""
        self._make_user(db)

        mock_redis.get.side_effect = lambda key: {
            "attempts_v@test.com": "5",
            "code_v@test.com": "123456",
        }.get(key)

        result = verify_code(db, "v@test.com", "123456")

        assert result is False
        mock_redis.delete.assert_any_call("code_v@test.com")
        mock_redis.delete.assert_any_call("attempts_v@test.com")

    @patch("services.auth_service.redis_client")
    def test_tp_as17_expired_code_returns_false(self, mock_redis, db):
        """TP-AS17: Expired code (stored=None) returns False."""
        self._make_user(db)

        mock_redis.get.side_effect = lambda key: {
            "attempts_v@test.com": None,
            "code_v@test.com": None,
        }.get(key)

        result = verify_code(db, "v@test.com", "123456")
        assert result is False

    @patch("services.auth_service.redis_client")
    def test_tp_as18_user_not_found_returns_false(self, mock_redis, db):
        """TP-AS18: User not found in DB returns False."""
        mock_redis.get.side_effect = lambda key: {
            "attempts_nobody@test.com": None,
            "code_nobody@test.com": "123456",
        }.get(key)

        result = verify_code(db, "nobody@test.com", "123456")
        assert result is False
