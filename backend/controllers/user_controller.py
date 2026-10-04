from flask import request, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config.database import execute_query, log_audit
from backend.utils.responses import success_response, error_response
from backend.services.auth_service import AuthService
from backend.utils.validators import sanitize_input, is_valid_email


class UserController:
    @staticmethod
    def get_users():
        """
        Admin only: list all users with search, role, status filters, and pagination.
        """
        try:
            limit = int(request.args.get("limit", 20))
            page = int(request.args.get("page", 1))
            search = (request.args.get("search") or "").strip().lower()
            role_filter = (request.args.get("role") or "").strip().lower()
            status_filter = (request.args.get("status") or "").strip().lower()

            offset = (page - 1) * limit
            where_clauses = []
            params = []

            if search:
                where_clauses.append("(LOWER(name) LIKE %s OR LOWER(email) LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            if role_filter in ("admin", "user"):
                where_clauses.append("role = %s")
                params.append(role_filter)

            if status_filter in ("active", "inactive", "blocked"):
                where_clauses.append("status = %s")
                params.append(status_filter)

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_query = f"SELECT COUNT(*) as total FROM users {where_str}"
            total_res = execute_query(count_query, params, fetch_one=True)
            total = total_res["result"]["total"] if total_res["result"] else 0

            data_query = f"""
                SELECT id, name, email, role, status, created_at, updated_at
                FROM users
                {where_str}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            data_params = list(params) + [limit, offset]
            users_res = execute_query(data_query, data_params, fetch_all=True)

            return success_response({
                "items": users_res["result"] or [],
                "total": total,
                "page": page,
                "limit": limit
            }, message="Users list retrieved successfully")
        except Exception as e:
            return error_response(f"Failed to fetch users: {str(e)}", status_code=500)

    @staticmethod
    def get_user_by_id(user_id):
        """
        Admin or current user profile.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if curr_user["role"] != "admin" and curr_user["id"] != int(user_id):
                return error_response("Forbidden: Access denied", status_code=403)

            query = """
                SELECT u.id, u.name, u.email, u.role, u.status, u.created_at, u.updated_at,
                       s.phone, s.department, s.bio, s.language, s.appearance, s.email_notifications, s.security_alerts
                FROM users u
                LEFT JOIN user_settings s ON u.id = s.user_id
                WHERE u.id = %s
                LIMIT 1
            """
            res = execute_query(query, (user_id,), fetch_one=True)
            if not res["result"]:
                return error_response("User not found", status_code=404)

            return success_response(res["result"], message="User details retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch user details: {str(e)}", status_code=500)

    @staticmethod
    def create_user():
        """
        Admin only: create a new user or administrator securely.
        """
        try:
            data = request.get_json(silent=True) or {}
            name = sanitize_input(data.get("name") or "")
            email = (data.get("email") or "").strip().lower()
            password = data.get("password") or ""
            role = "user"
            status = (data.get("status") or "active").strip().lower()
            phone = sanitize_input(data.get("phone") or "")
            department = sanitize_input(data.get("department") or "General")

            if not name or len(name) < 2:
                return error_response("Full name is required (min 2 characters)", status_code=400)
            if not email or not is_valid_email(email):
                return error_response("Valid email address is required", status_code=400)
            if not password or len(password) < 6:
                return error_response("Password must be at least 6 characters long", status_code=400)
            if status not in ("active", "inactive", "blocked"):
                status = "active"

            existing = AuthService.get_user_by_email(email)
            if existing:
                return error_response("An account with this email address already exists.", status_code=409)

            hashed_password = generate_password_hash(password)
            insert_query = """
                INSERT INTO users (name, email, password_hash, role, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(insert_query, (name, email, hashed_password, role, status), commit=True)
            new_id = res["last_id"]

            # Create default user_settings
            settings_query = """
                INSERT OR IGNORE INTO user_settings (user_id, phone, department)
                VALUES (%s, %s, %s)
            """
            execute_query(settings_query, (new_id, phone, department), commit=True)

            curr_user = getattr(g, "current_user", None)
            log_audit(curr_user["id"] if curr_user else None, "CREATE", "USERS", new_id, f"Admin created user {email} (role: {role})")

            created_user = AuthService.get_user_by_id(new_id)
            return success_response(created_user, message="User created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Failed to create user: {str(e)}", status_code=500)

    @staticmethod
    def update_user(user_id):
        """
        Admin only: update user information, status, or role.
        Protects admin from accidentally de-admining themselves.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            data = request.get_json(silent=True) or {}
            name = sanitize_input(data.get("name") or "")
            email = (data.get("email") or "").strip().lower()
            status = (data.get("status") or "").strip().lower()
            phone = sanitize_input(data.get("phone") or "")
            department = sanitize_input(data.get("department") or "")
            bio = sanitize_input(data.get("bio") or "")

            target = AuthService.get_user_by_id(user_id)
            if not target:
                return error_response("User not found", status_code=404)

            if curr_user and curr_user["id"] == int(user_id):
                if status and status != "active":
                    return error_response("You cannot deactivate or block your own active session.", status_code=400)

            updates = []
            params = []

            if name:
                updates.append("name = %s")
                params.append(name)
            if email and email != target["email"]:
                if not is_valid_email(email):
                    return error_response("Invalid email format", status_code=400)
                existing = AuthService.get_user_by_email(email)
                if existing and existing["id"] != int(user_id):
                    return error_response("Email is already in use by another user", status_code=409)
                updates.append("email = %s")
                params.append(email)
            if status in ("active", "inactive", "blocked"):
                updates.append("status = %s")
                params.append(status)

            if data.get("password"):
                if len(data.get("password")) < 6:
                    return error_response("New password must be at least 6 characters", status_code=400)
                updates.append("password_hash = %s")
                params.append(generate_password_hash(data.get("password")))

            if updates:
                params.append(user_id)
                upd_query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                execute_query(upd_query, params, commit=True)

            # Update settings / phone / department
            set_res = execute_query("SELECT id FROM user_settings WHERE user_id = %s", (user_id,), fetch_one=True)
            if set_res["result"]:
                execute_query("UPDATE user_settings SET phone = %s, department = %s, bio = %s WHERE user_id = %s", (phone, department, bio, user_id), commit=True)
            else:
                execute_query("INSERT INTO user_settings (user_id, phone, department, bio) VALUES (%s, %s, %s, %s)", (user_id, phone, department, bio), commit=True)

            log_audit(curr_user["id"] if curr_user else None, "UPDATE", "USERS", user_id, f"Updated user profile/status for ID {user_id}")
            updated = AuthService.get_user_by_id(user_id)
            return success_response(updated, message="User updated successfully")
        except Exception as e:
            return error_response(f"Failed to update user: {str(e)}", status_code=500)

    @staticmethod
    def update_status(user_id):
        """
        Admin only: activate, deactivate, or block user.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            data = request.get_json(silent=True) or {}
            new_status = (data.get("status") or "").strip().lower()

            if new_status not in ("active", "inactive", "blocked"):
                return error_response("Status must be 'active', 'inactive', or 'blocked'", status_code=400)

            if curr_user and curr_user["id"] == int(user_id) and new_status != "active":
                return error_response("You cannot change the status of your own account.", status_code=400)

            execute_query("UPDATE users SET status = %s WHERE id = %s", (new_status, user_id), commit=True)
            log_audit(curr_user["id"] if curr_user else None, "STATUS_CHANGE", "USERS", user_id, f"Changed user status to {new_status} for ID {user_id}")
            return success_response(message=f"User status updated to {new_status}")
        except Exception as e:
            return error_response(f"Failed to update status: {str(e)}", status_code=500)

    @staticmethod
    def delete_user(user_id):
        """
        Admin only: soft-deactivate or delete user safely.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if curr_user and curr_user["id"] == int(user_id):
                return error_response("You cannot delete your own active account.", status_code=400)

            # Soft delete / deactivate
            execute_query("UPDATE users SET status = 'inactive' WHERE id = %s", (user_id,), commit=True)
            log_audit(curr_user["id"] if curr_user else None, "DEACTIVATE", "USERS", user_id, f"Deactivated user ID {user_id}")
            return success_response(message="User deactivated successfully")
        except Exception as e:
            return error_response(f"Failed to deactivate user: {str(e)}", status_code=500)

    @staticmethod
    def get_profile():
        """
        Current authenticated user profile + preferences.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            query = """
                SELECT u.id, u.name, u.email, u.role, u.status, u.created_at,
                       s.phone, s.department, s.bio, s.language, s.appearance, s.email_notifications, s.security_alerts, s.activity_digest
                FROM users u
                LEFT JOIN user_settings s ON u.id = s.user_id
                WHERE u.id = %s
                LIMIT 1
            """
            res = execute_query(query, (curr_user["id"],), fetch_one=True)
            return success_response(res["result"] or curr_user, message="User profile retrieved")
        except Exception as e:
            return error_response(f"Failed to retrieve profile: {str(e)}", status_code=500)

    @staticmethod
    def update_profile():
        """
        Current authenticated user updating own profile info.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            name = sanitize_input(data.get("name") or "")
            phone = sanitize_input(data.get("phone") or "")
            department = sanitize_input(data.get("department") or "")
            bio = sanitize_input(data.get("bio") or "")

            if name and len(name) >= 2:
                execute_query("UPDATE users SET name = %s WHERE id = %s", (name, curr_user["id"]), commit=True)

            set_res = execute_query("SELECT id FROM user_settings WHERE user_id = %s", (curr_user["id"],), fetch_one=True)
            if set_res["result"]:
                execute_query("UPDATE user_settings SET phone = %s, department = %s, bio = %s WHERE user_id = %s", (phone, department, bio, curr_user["id"]), commit=True)
            else:
                execute_query("INSERT INTO user_settings (user_id, phone, department, bio) VALUES (%s, %s, %s, %s)", (curr_user["id"], phone, department, bio), commit=True)

            log_audit(curr_user["id"], "UPDATE_PROFILE", "USER", curr_user["id"], "User updated own profile information")
            updated = AuthService.get_user_by_id(curr_user["id"])
            return success_response(updated, message="Profile updated successfully")
        except Exception as e:
            return error_response(f"Failed to update profile: {str(e)}", status_code=500)

    @staticmethod
    def change_password():
        """
        Current authenticated user changes own password.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            current_pass = data.get("current_password") or ""
            new_pass = data.get("new_password") or ""
            confirm_pass = data.get("confirm_password") or data.get("confirm_new_password") or ""

            if not current_pass or not new_pass:
                return error_response("Current password and new password are required", status_code=400)
            if len(new_pass) < 6:
                return error_response("New password must be at least 6 characters long", status_code=400)
            if new_pass != confirm_pass:
                return error_response("New password confirmation does not match", status_code=400)

            # Verify current password
            user_full = AuthService.get_user_by_email(curr_user["email"])
            if not user_full or not AuthService.verify_password(current_pass, user_full["password_hash"]):
                return error_response("Current password is incorrect", status_code=400)

            hashed = generate_password_hash(new_pass)
            execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (hashed, curr_user["id"]), commit=True)
            log_audit(curr_user["id"], "CHANGE_PASSWORD", "SECURITY", curr_user["id"], "User successfully changed password")

            return success_response(message="Password changed successfully")
        except Exception as e:
            return error_response(f"Failed to change password: {str(e)}", status_code=500)
