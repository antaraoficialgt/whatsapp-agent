import pytest
from auth import AuthManager
from database import Database

def test_hash_password(auth_manager):
    password = "test_password_123"
    hashed = auth_manager.hash_password(password)
    assert hashed != password
    assert auth_manager.verify_password(password, hashed)

def test_verify_password_wrong(auth_manager):
    password = "test_password_123"
    hashed = auth_manager.hash_password(password)
    assert not auth_manager.verify_password("wrong_password", hashed)

def test_create_user(auth_manager):
    user = auth_manager.create_user("test@test.com", "password123", "Test User")
    assert user is not None
    assert user["email"] == "test@test.com"
    assert user["name"] == "Test User"

def test_create_user_duplicate_email(auth_manager):
    auth_manager.create_user("test@test.com", "password123", "Test User")
    user = auth_manager.create_user("test@test.com", "password456", "Another User")
    assert user is None

def test_authenticate_user(auth_manager):
    auth_manager.create_user("test@test.com", "password123", "Test User")
    user = auth_manager.authenticate_user("test@test.com", "password123")
    assert user is not None
    assert user["email"] == "test@test.com"

def test_authenticate_user_wrong_password(auth_manager):
    auth_manager.create_user("test@test.com", "password123", "Test User")
    user = auth_manager.authenticate_user("test@test.com", "wrong_password")
    assert user is None

def test_authenticate_user_not_found(auth_manager):
    user = auth_manager.authenticate_user("nonexistent@test.com", "password123")
    assert user is None

def test_create_api_token(auth_manager):
    token = auth_manager.create_api_token(1)
    assert token.startswith("token_1_")
    assert len(token) > 20

def test_get_user_from_token(auth_manager):
    auth_manager.create_user("test@test.com", "password123", "Test User")
    user = auth_manager.authenticate_user("test@test.com", "password123")
    token = auth_manager.create_api_token(user["id"])

    retrieved_user = auth_manager.get_user_from_token(token)
    assert retrieved_user is not None
    assert retrieved_user["email"] == "test@test.com"

def test_get_user_from_invalid_token(auth_manager):
    user = auth_manager.get_user_from_token("invalid_token")
    assert user is None

def test_get_user_from_token_invalid_format(auth_manager):
    user = auth_manager.get_user_from_token("no_prefix_token")
    assert user is None
