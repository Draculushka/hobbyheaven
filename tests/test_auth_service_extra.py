import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from services.auth_service import verify_deletion_code, verify_code
from models import User

class TestAuthServiceExtra:
    @patch("services.auth_service.redis_client")
    def test_verify_deletion_code_success(self, mock_redis):
        mock_redis.get.return_value = "123456"
        result = verify_deletion_code("test@test.com", "123456")
        assert result is True
        mock_redis.delete.assert_called_once_with("code_test@test.com")

    @patch("services.auth_service.redis_client")
    def test_verify_deletion_code_wrong_code(self, mock_redis):
        mock_redis.get.return_value = "123456"
        result = verify_deletion_code("test@test.com", "000000")
        assert result is False
        mock_redis.delete.assert_not_called()

    @patch("services.auth_service.redis_client")
    def test_verify_deletion_code_no_code(self, mock_redis):
        mock_redis.get.return_value = None
        result = verify_deletion_code("test@test.com", "123456")
        assert result is False
        mock_redis.delete.assert_not_called()

    @patch("services.auth_service.redis_client")
    def test_verify_code_with_deleted_user(self, mock_redis, db):
        from core.security import get_password_hash
        user = User(
            email="deleted@test.com", 
            hashed_password=get_password_hash("pw"),
            deleted_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()

        mock_redis.get.side_effect = lambda key: {
            "attempts_deleted@test.com": None,
            "code_deleted@test.com": "123456",
        }.get(key)

        result = verify_code(db, "deleted@test.com", "123456")
        assert result is False
