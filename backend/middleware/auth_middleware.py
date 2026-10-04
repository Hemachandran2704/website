from functools import wraps
from flask import request, g, session
from backend.services.auth_service import AuthService
from backend.utils.responses import error_response


def get_token_from_request():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1].strip()
    return None


def require_auth(admin_only=False):
    """
    Decorator to protect routes requiring authentication and optional admin authorization.
    Supports both JWT Authorization Bearer tokens and Flask session-based authentication.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = None
            token = get_token_from_request()
            if token:
                payload = AuthService.decode_token(token)
                if payload:
                    user = AuthService.get_user_by_id(payload.get("id"))
                    
            # If no valid token found in headers, check Flask session
            if not user and session.get("user_id"):
                user = AuthService.get_user_by_id(session.get("user_id"))

            if not user:
                return error_response("Authentication required. Please log in.", status_code=401)
                
            if user.get("status") != "active":
                return error_response("User account is inactive or no longer exists.", status_code=401)
                
            if admin_only and user.get("role") != "admin":
                return error_response("Forbidden: Administrator privileges required.", status_code=403)
                
            g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def optional_auth():
    """
    Decorator that attaches current_user if valid token or session provided, else None.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            g.current_user = None
            user = None
            token = get_token_from_request()
            if token:
                payload = AuthService.decode_token(token)
                if payload:
                    user = AuthService.get_user_by_id(payload.get("id"))
            
            if not user and session.get("user_id"):
                user = AuthService.get_user_by_id(session.get("user_id"))
                
            if user and user.get("status") == "active":
                g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
