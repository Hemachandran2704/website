from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class IframeController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
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
                
            if search:
                where_clauses.append("(title LIKE %s OR url LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, title, url, width, height, allow_fullscreen, status,
                       created_at, updated_at
                FROM iframes
                {where_sql}
                ORDER BY id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="iFrames retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching iframes: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(iframe_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, title, url, width, height, allow_fullscreen, status,
                       created_at, updated_at
                FROM iframes WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (iframe_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("iFrame not found", status_code=404)
            return success_response(res["result"], message="iFrame retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching iframe: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_iframe(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            url = data.get("url").strip()
            width = (data.get("width") or "100%").strip()
            height = (data.get("height") or "400px").strip()
            allow_fullscreen = 1 if data.get("allow_fullscreen", True) in (True, 1, "1", "true") else 0
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO iframes (user_id, title, url, width, height, allow_fullscreen, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, url, width, height, allow_fullscreen, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "IFRAMES", new_id, f"Created iframe embed '{title}'")
            
            return success_response({"id": new_id, "title": title}, message="iFrame created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating iframe: {str(e)}", status_code=500)

    @staticmethod
    def update(iframe_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM iframes WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (iframe_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("iFrame not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_iframe(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            url = data.get("url").strip()
            width = (data.get("width") or "100%").strip()
            height = (data.get("height") or "400px").strip()
            allow_fullscreen = 1 if data.get("allow_fullscreen", True) in (True, 1, "1", "true") else 0
            status = data.get("status", "active")
            
            query = """
                UPDATE iframes
                SET title = %s, url = %s, width = %s, height = %s, allow_fullscreen = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title, url, width, height, allow_fullscreen, status, iframe_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "IFRAMES", iframe_id, f"Updated iframe embed '{title}' (id: {iframe_id})")
            
            return success_response({"id": iframe_id, "title": title}, message="iFrame updated successfully")
        except Exception as e:
            return error_response(f"Error updating iframe: {str(e)}", status_code=500)

    @staticmethod
    def delete(iframe_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM iframes WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (iframe_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("iFrame not found", status_code=404)
                
            title = existing["result"]["title"]
            execute_query("DELETE FROM iframes WHERE id = %s AND user_id = %s", (iframe_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "IFRAMES", iframe_id, f"Deleted iframe embed '{title}' (id: {iframe_id})")
            
            return success_response(message="iFrame deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting iframe: {str(e)}", status_code=500)
