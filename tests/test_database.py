import pytest
from database import Database

def test_create_user(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    assert user["email"] == "test@test.com"
    assert user["name"] == "Test User"
    assert user["id"] > 0

def test_get_user_by_email(test_db):
    test_db.create_user("test@test.com", "hashed_password", "Test User")
    user = test_db.get_user_by_email("test@test.com")
    assert user is not None
    assert user["email"] == "test@test.com"

def test_get_user_by_id(test_db):
    created_user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    user = test_db.get_user_by_id(created_user["id"])
    assert user is not None
    assert user["email"] == "test@test.com"

def test_create_subscription(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    subscription = test_db.create_subscription(user["id"], "free")
    assert subscription is not None
    assert subscription["plan"] == "free"
    assert subscription["max_customers"] == 1

def test_upgrade_subscription(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    test_db.create_subscription(user["id"], "free")
    success = test_db.upgrade_subscription(user["id"], "pro")
    assert success
    subscription = test_db.get_subscription_by_user(user["id"])
    assert subscription["plan"] == "pro"
    assert subscription["max_customers"] == 5

def test_create_customer(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    customer = test_db.create_customer(
        user_id=user["id"],
        name="Test Business",
        phone_number_id="1234567890",
        access_token="token123",
        api_key="key123"
    )
    assert customer["name"] == "Test Business"
    assert customer["id"] > 0

def test_get_customers_by_user(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    test_db.create_customer(
        user_id=user["id"],
        name="Business 1",
        phone_number_id="1234567890",
        access_token="token123",
        api_key="key123"
    )
    test_db.create_customer(
        user_id=user["id"],
        name="Business 2",
        phone_number_id="9876543210",
        access_token="token456",
        api_key="key456"
    )
    customers = test_db.get_customers_by_user(user["id"])
    assert len(customers) == 2

def test_save_conversation(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    customer = test_db.create_customer(
        user_id=user["id"],
        name="Test Business",
        phone_number_id="1234567890",
        access_token="token123",
        api_key="key123"
    )
    conv_id = test_db.save_conversation(
        customer_id=customer["id"],
        sender_phone="5551234567",
        message_text="Hello",
        response_text="Hi",
        response_time_ms=100
    )
    assert conv_id > 0

def test_get_conversation_history(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    customer = test_db.create_customer(
        user_id=user["id"],
        name="Test Business",
        phone_number_id="1234567890",
        access_token="token123",
        api_key="key123"
    )
    test_db.save_conversation(
        customer_id=customer["id"],
        sender_phone="5551234567",
        message_text="Hello",
        response_text="Hi"
    )
    history = test_db.get_conversation_history(customer["id"], "5551234567")
    assert len(history) == 1

def test_update_analytics(test_db):
    user = test_db.create_user("test@test.com", "hashed_password", "Test User")
    customer = test_db.create_customer(
        user_id=user["id"],
        name="Test Business",
        phone_number_id="1234567890",
        access_token="token123",
        api_key="key123"
    )
    success = test_db.update_analytics(customer["id"], response_time_ms=100)
    assert success
    analytics = test_db.get_analytics(customer["id"], days=30)
    assert len(analytics) >= 1

def test_plan_config():
    free_config = Database._get_plan_config("free")
    assert free_config["max_customers"] == 1
    assert free_config["has_basic_dashboard"] == 1
    assert free_config["has_advanced_dashboard"] == 0

    pro_config = Database._get_plan_config("pro")
    assert pro_config["max_customers"] == 5
    assert pro_config["has_advanced_dashboard"] == 1

    enterprise_config = Database._get_plan_config("enterprise")
    assert enterprise_config["max_customers"] == 999
