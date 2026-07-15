from datetime import timedelta

import jwt
import pytest

from auth.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"


def test_verify_password_accepts_correct_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("wrong password", hashed) is False


def test_verify_password_handles_malformed_hash_gracefully():
    # e.g. an OAuth-only account with no real password hash set
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False


def test_access_token_round_trips():
    token = create_access_token(user_id=42, role="user")
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_refresh_token_has_refresh_type():
    token = create_refresh_token(user_id=42, role="admin")
    payload = decode_token(token)
    assert payload["type"] == REFRESH_TOKEN_TYPE


def test_decode_expired_token_raises():
    expired = _create_token(1, "user", ACCESS_TOKEN_TYPE, timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)


def test_decode_tampered_token_raises():
    token = create_access_token(user_id=1, role="user")
    with pytest.raises(jwt.PyJWTError):
        decode_token(token + "tampered")


def test_hash_token_is_deterministic_and_one_way():
    token = "some-refresh-token-value"
    hashed = hash_token(token)
    assert hashed == hash_token(token)
    assert hashed != token
