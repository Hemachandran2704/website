from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class PopupController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            trigger_param = request.args.get("trigger_type", "").strip()
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            owner_clause, params = readable_owner_scope(user)
            where_clauses = [owner_clause]
            
            if not user or status_param == "active":
                where_clauses.append("status = %s")
                params.append("active")
            elif status_param == "inactive":
                where_clauses.append("status = %s")
                params.append("inactive")
                
            if trigger_param:
                where_clauses.append("trigger_type = %s")
                params.append(trigger_param)
                
            if search:
                where_clauses.append("(title LIKE %s OR content LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, title, content, trigger_type, status,
                       created_at, updated_at
                FROM popups
                {where_sql}
                ORDER BY id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="Popups retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching popups: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(popup_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, title, content, trigger_type, status,
                       created_at, updated_at
                FROM popups WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (popup_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Popup not found", status_code=404)
            return success_response(res["result"], message="Popup retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching popup: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_popup(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            trigger_type = data.get("trigger_type", "button_click")
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO popups (user_id, title, content, trigger_type, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, content, trigger_type, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "POPUPS", new_id, f"Created popup '{title}' ({trigger_type})")
            
            return success_response({"id": new_id, "title": title}, message="Popup created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating popup: {str(e)}", status_code=500)

    @staticmethod
    def update(popup_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM popups WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (popup_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Popup not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_popup(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            trigger_type = data.get("trigger_type", "button_click")
            status = data.get("status", "active")
            
            query = """
                UPDATE popups
                SET title = %s, content = %s, trigger_type = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title, content, trigger_type, status, popup_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "POPUPS", popup_id, f"Updated popup '{title}' (id: {popup_id})")
            
            return success_response({"id": popup_id, "title": title}, message="Popup updated successfully")
        except Exception as e:
            return error_response(f"Error updating popup: {str(e)}", status_code=500)

    @staticmethod
    def delete(popup_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM popups WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (popup_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Popup not found", status_code=404)
                
            title = existing["result"]["title"]
            execute_query("DELETE FROM popups WHERE id = %s AND user_id = %s", (popup_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "POPUPS", popup_id, f"Deleted popup '{title}' (id: {popup_id})")
            
            return success_response(message="Popup deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting popup: {str(e)}", status_code=500)
