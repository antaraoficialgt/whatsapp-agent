import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from database import db
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthManager:
    def __init__(self, database=None):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this")
        self.token_expiration_hours = 24
        self.db = database or db

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, email: str, password: str, name: str) -> Optional[Dict]:
        """Create a new user with email and password."""
        try:
            existing_user = self.db.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None

            password_hash = self.hash_password(password)
            user = self.db.create_user(email, password_hash, name)

            self.db.create_subscription(user["id"], plan="free")

            logger.info(f"User created: {email}")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password."""
        try:
            user = self.db.get_user_by_email(email)
            if not user:
                return None

            if not self.verify_password(password, user["password_hash"]):
                return None

            subscription = self.db.get_subscription_by_user(user["id"])

            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "subscription": subscription
            }

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None

    def create_api_token(self, user_id: int) -> str:
        """Create a simple JWT-like token for API access."""
        token = f"token_{user_id}_{secrets.token_urlsafe(32)}"
        return token

    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Extract user ID from token and get user data."""
        try:
            if not token.startswith("token_"):
                return None

            parts = token.split("_", 2)
            if len(parts) < 2:
                return None

            user_id = int(parts[1])
            user = self.db.get_user_by_id(user_id)

            if not user:
                return None

            subscription = self.db.get_subscription_by_user(user_id)

            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "subscription": subscription
            }

        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            return None

auth_manager = AuthManager()
