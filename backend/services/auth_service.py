import os
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from backend.config.database import execute_query

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-magnus-cms-key-change-in-production-2026")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))


class AuthService:
    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def verify_password(plain_password, password_hash):
        return check_password_hash(password_hash, plain_password)

    @staticmethod
    def generate_token(user):
        payload = {
            "sub": str(user["id"]),
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": "user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.datetime.now(datetime.timezone.utc)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_token(token):
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    @staticmethod
    def get_user_by_email(email):
        query = "SELECT id, name, email, password_hash, role, status, created_at, updated_at FROM users WHERE email = %s LIMIT 1"
        res = execute_query(query, (email.strip().lower(),), fetch_one=True)
        return res["result"]

    @staticmethod
    def get_user_by_id(user_id):
        query = "SELECT id, name, email, role, status, created_at, updated_at FROM users WHERE id = %s LIMIT 1"
        res = execute_query(query, (user_id,), fetch_one=True)
        return res["result"]

    @classmethod
    def authenticate(cls, email, password):
        user = cls.get_user_by_email(email)
        if not user:
            return None, "Invalid email or password."
        if user["status"] != "active":
            return None, "Account is disabled. Please contact administrator."
        if not cls.verify_password(password, user["password_hash"]):
            return None, "Invalid email or password."
            
        token = cls.generate_token(user)
        safe_user = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": "user",
            "status": user["status"]
        }
        return {"token": token, "user": safe_user}, None

    @classmethod
    def register_user(cls, name, email, password):
        clean_email = email.strip().lower()
        existing = cls.get_user_by_email(clean_email)
        if existing:
            return None, "An account with this email address already exists. Please sign in instead."

        hashed_password = cls.hash_password(password)
        query = """
            INSERT INTO users (name, email, password_hash, status)
            VALUES (%s, %s, %s, 'active')
        """
        res = execute_query(query, (name.strip(), clean_email, hashed_password), commit=True)
        new_id = res["last_id"]

        # Initialize default user_settings
        try:
            execute_query("""
                INSERT OR IGNORE INTO user_settings (user_id, language, appearance)
                VALUES (%s, 'en', 'light')
            """, (new_id,), commit=True)
            # Add welcome notification
            execute_query("""
                INSERT INTO notifications (user_id, title, message, type, status)
                VALUES (%s, 'Welcome to Magnus CMS', 'Your account has been created. Start by exploring your dashboard or opening a support ticket.', 'info', 'active')
            """, (new_id,), commit=True)
        except Exception:
            pass

        new_user = cls.get_user_by_id(new_id)
        if not new_user:
            return None, "Failed to create user account. Please try again."

        safe_user = {
            "id": new_user["id"],
            "name": new_user["name"],
            "email": new_user["email"],
            "role": "user",
            "status": new_user["status"]
        }
        return {"user": safe_user}, None

