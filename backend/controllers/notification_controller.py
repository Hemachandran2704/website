from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.utils.responses import success_response, error_response


class NotificationController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            type_param = request.args.get("type", "").strip().lower()
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            is_admin = user and user.get("role") == "admin"
            
            where_clauses = []
            params = []
            
            if not is_admin and user:
                # Regular user sees broadcast (user_id IS NULL) and own notifications
                where_clauses.append("(user_id IS NULL OR user_id = %s)")
                params.append(user["id"])
            
            if status_param in ("active", "inactive", "read"):
                where_clauses.append("status = %s")
                params.append(status_param)
            elif not is_admin:
                where_clauses.append("status != 'inactive'")
                
            if type_param and type_param != "all":
                where_clauses.append("type = %s")
                params.append(type_param)
                
            if search:
                where_clauses.append("(title LIKE %s OR message LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, title, message, type, status, created_at, updated_at
                FROM notifications
                {where_sql}
                ORDER BY id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            return success_response(res["result"] or [], message="Notifications retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching notifications: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(notif_id):
        try:
            query = """
                SELECT id, user_id, title, message, type, status, created_at, updated_at
                FROM notifications WHERE id = %s LIMIT 1
            """
            res = execute_query(query, (notif_id,), fetch_one=True)
            if not res["result"]:
                return error_response("Notification not found", status_code=404)
            return success_response(res["result"], message="Notification retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching notification: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_notification(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            message = data.get("message").strip()
            notif_type = data.get("type", "info").lower().strip()
            status = data.get("status", "active")
            target_user_id = data.get("user_id")
            
            query = """
                INSERT INTO notifications (user_id, title, message, type, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (target_user_id, title, message, notif_type, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "NOTIFICATIONS", new_id, f"Created notification '{title}' [{notif_type}]")
            
            return success_response({"id": new_id, "title": title}, message="Notification created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating notification: {str(e)}", status_code=500)

    @staticmethod
    def update(notif_id):
        try:
            check_q = "SELECT id, title FROM notifications WHERE id = %s"
            existing = execute_query(check_q, (notif_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Notification not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_notification(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            message = data.get("message").strip()
            notif_type = data.get("type", "info").lower().strip()
            status = data.get("status", "active")
            
            query = """
                UPDATE notifications
                SET title = %s, message = %s, type = %s, status = %s
                WHERE id = %s
            """
            execute_query(query, (title, message, notif_type, status, notif_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "NOTIFICATIONS", notif_id, f"Updated notification '{title}' (id: {notif_id})")
            
            return success_response({"id": notif_id, "title": title}, message="Notification updated successfully")
        except Exception as e:
            return error_response(f"Error updating notification: {str(e)}", status_code=500)

    @staticmethod
    def mark_as_read(notif_id):
        try:
            execute_query("UPDATE notifications SET status = 'read' WHERE id = %s", (notif_id,), commit=True)
            return success_response(message="Notification marked as read")
        except Exception as e:
            return error_response(f"Error marking notification as read: {str(e)}", status_code=500)

    @staticmethod
    def delete(notif_id):
        try:
            check_q = "SELECT id, title FROM notifications WHERE id = %s"
            existing = execute_query(check_q, (notif_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Notification not found", status_code=404)
                
            notif_title = existing["result"]["title"]
            delete_q = "DELETE FROM notifications WHERE id = %s"
            execute_query(delete_q, (notif_id,), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "NOTIFICATIONS", notif_id, f"Deleted notification '{notif_title}' (id: {notif_id})")
            
            return success_response(message="Notification deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting notification: {str(e)}", status_code=500)
