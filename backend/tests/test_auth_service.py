import pytest
import time
from auth import (
    validate_password,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestValidatePassword:
    def test_valid_password(self):
        ok, msg = validate_password("Abc12345")
        assert ok is True
        assert msg == ""

    def test_too_short(self):
        ok, msg = validate_password("Ab12")
        assert ok is False
        assert "8文字" in msg

    def test_no_letters(self):
        ok, msg = validate_password("12345678")
        assert ok is False
        assert "英字" in msg

    def test_no_numbers(self):
        ok, msg = validate_password("Abcdefgh")
        assert ok is False
        assert "数字" in msg

    def test_minimum_valid(self):
        ok, msg = validate_password("A1b2c3d4")
        assert ok is True


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("test1234Password")
        assert verify_password("test1234Password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correctPassword1")
        assert verify_password("wrongPassword1", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("samePassword1")
        h2 = hash_password("samePassword1")
        assert h1 != h2  # bcrypt generates different salts


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token(user_id=1, username="tanaka", role="admin")
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "tanaka"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "jti" in payload

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            decode_access_token("invalid.token.here")

    def test_token_has_jti(self):
        token = create_access_token(user_id=1, username="test", role="staff")
        payload = decode_access_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) > 0
