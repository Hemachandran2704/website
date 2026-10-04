from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.utils.responses import success_response, error_response
from backend.utils.validators import sanitize_input


class AnnouncementController:
    @staticmethod
    def get_announcements():
        try:
            curr_user = getattr(g, "current_user", None)
            is_admin = curr_user and curr_user.get("role") == "admin"
            status_filter = (request.args.get("status") or ("" if is_admin else "active")).strip().lower()

            where_clauses = []
            params = []

            if status_filter in ("active", "inactive"):
                where_clauses.append("status = %s")
                params.append(status_filter)

            if not is_admin:
                where_clauses.append("(target_role = 'all' OR target_role = 'user')")

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            query = f"SELECT * FROM announcements {where_str} ORDER BY id DESC"
            res = execute_query(query, params, fetch_all=True)
            return success_response(res["result"] or [], message="Announcements retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch announcements: {str(e)}", status_code=500)

    @staticmethod
    def create_announcement():
        try:
            curr_user = getattr(g, "current_user", None)
            data = request.get_json(silent=True) or {}
            title = sanitize_input(data.get("title") or "")
            message = sanitize_input(data.get("message") or "")
            priority = (data.get("priority") or "normal").strip().lower()
            target_role = (data.get("target_role") or "all").strip().lower()

            if not title or len(title) < 2:
                return error_response("Title is required", status_code=400)
            if not message:
                return error_response("Message content is required", status_code=400)

            query = """
                INSERT INTO announcements (title, message, priority, target_role, status)
                VALUES (%s, %s, %s, %s, 'active')
            """
            res = execute_query(query, (title, message, priority, target_role), commit=True)
            new_id = res["last_id"]
            log_audit(curr_user["id"] if curr_user else None, "CREATE_ANNOUNCEMENT", "SYSTEM", new_id, f"Created announcement: {title}")
            return success_response({"id": new_id, "title": title}, message="Announcement created", status_code=201)
        except Exception as e:
            return error_response(f"Failed to create announcement: {str(e)}", status_code=500)

    @staticmethod
    def update_announcement(ann_id):
        try:
            curr_user = getattr(g, "current_user", None)
            data = request.get_json(silent=True) or {}
            title = sanitize_input(data.get("title") or "")
            message = sanitize_input(data.get("message") or "")
            priority = (data.get("priority") or "normal").strip().lower()
            target_role = (data.get("target_role") or "all").strip().lower()
            status = (data.get("status") or "active").strip().lower()

            query = """
                UPDATE announcements
                SET title = %s, message = %s, priority = %s, target_role = %s, status = %s
                WHERE id = %s
            """
            execute_query(query, (title, message, priority, target_role, status, ann_id), commit=True)
            log_audit(curr_user["id"] if curr_user else None, "UPDATE_ANNOUNCEMENT", "SYSTEM", ann_id, f"Updated announcement #{ann_id}")
            return success_response(message="Announcement updated successfully")
        except Exception as e:
            return error_response(f"Failed to update announcement: {str(e)}", status_code=500)

    @staticmethod
    def delete_announcement(ann_id):
        try:
            curr_user = getattr(g, "current_user", None)
            execute_query("DELETE FROM announcements WHERE id = %s", (ann_id,), commit=True)
            log_audit(curr_user["id"] if curr_user else None, "DELETE_ANNOUNCEMENT", "SYSTEM", ann_id, f"Deleted announcement #{ann_id}")
            return success_response(message="Announcement deleted successfully")
        except Exception as e:
            return error_response(f"Failed to delete announcement: {str(e)}", status_code=500)
