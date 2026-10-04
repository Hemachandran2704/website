from flask import request, g, session
from backend.services.auth_service import AuthService
from backend.services.validation_service import ValidationService
from backend.config.database import log_audit
from backend.utils.responses import success_response, error_response


class AuthController:
    @staticmethod
    def login():
        data = request.get_json(silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()
            
        is_valid, errors = ValidationService.validate_user_login(data)
        if not is_valid:
            return error_response("Validation failed", errors=errors, status_code=400)
            
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        
        auth_data, err = AuthService.authenticate(email, password)
        if err:
            return error_response(err, status_code=401)
            
        user = auth_data["user"]
        
        # Set Flask session
        session.permanent = True
        session["user_id"] = user["id"]
        session["user"] = user
        
        log_audit(user["id"], "LOGIN", "AUTH", user["id"], f"User {user['email']} logged in successfully")
        auth_data["redirect"] = "/dashboard"
            
        return success_response(auth_data, message="Login successful", status_code=200)

    @staticmethod
    def register():
        data = request.get_json(silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()
            
        is_valid, errors = ValidationService.validate_user_registration(data)
        if not is_valid:
            return error_response("Validation failed", errors=errors, status_code=400)
            
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        
        auth_data, err = AuthService.register_user(name, email, password)
        if err:
            status_code = 409 if "already exists" in err.lower() else 400
            return error_response(err, status_code=status_code)
            
        user = auth_data["user"]
        log_audit(user["id"], "REGISTER", "AUTH", user["id"], f"User {user['email']} registered successfully as user")
        auth_data["redirect"] = "/login?registered=1"
        return success_response(auth_data, message="Registration successful", status_code=201)

    @staticmethod
    def logout():
        user = getattr(g, "current_user", None)
        if not user and session.get("user_id"):
            user = AuthService.get_user_by_id(session.get("user_id"))
            
        if user:
            log_audit(user["id"], "LOGOUT", "AUTH", user["id"], f"User {user['email']} logged out")
            
        session.clear()
        return success_response(message="Logged out successfully")

    @staticmethod
    def me():
        user = getattr(g, "current_user", None)
        if not user and session.get("user_id"):
            user = AuthService.get_user_by_id(session.get("user_id"))
            
        if not user:
            return error_response("Unauthorized", status_code=401)
            
        safe_user = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": "user",
            "status": user["status"],
            "created_at": str(user.get("created_at", ""))
        }
        return success_response(safe_user, message="Current user profile retrieved")
