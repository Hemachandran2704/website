from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class TooltipController:
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
                where_clauses.append("(element_name LIKE %s OR content LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, element_name, content, position, status,
                       created_at, updated_at
                FROM tooltips
                {where_sql}
                ORDER BY id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="Tooltips retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching tooltips: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(tooltip_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, element_name, content, position, status,
                       created_at, updated_at
                FROM tooltips WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (tooltip_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Tooltip not found", status_code=404)
            return success_response(res["result"], message="Tooltip retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching tooltip: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_tooltip(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            element_name = data.get("element_name").strip()
            content = data.get("content").strip()
            position = data.get("position", "top")
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO tooltips (user_id, element_name, content, position, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, element_name, content, position, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "TOOLTIPS", new_id, f"Created tooltip for '{element_name}'")
            
            return success_response({"id": new_id, "element_name": element_name}, message="Tooltip created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating tooltip: {str(e)}", status_code=500)

    @staticmethod
    def update(tooltip_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, element_name FROM tooltips WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (tooltip_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Tooltip not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_tooltip(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            element_name = data.get("element_name").strip()
            content = data.get("content").strip()
            position = data.get("position", "top")
            status = data.get("status", "active")
            
            query = """
                UPDATE tooltips
                SET element_name = %s, content = %s, position = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (element_name, content, position, status, tooltip_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "TOOLTIPS", tooltip_id, f"Updated tooltip for '{element_name}' (id: {tooltip_id})")
            
            return success_response({"id": tooltip_id, "element_name": element_name}, message="Tooltip updated successfully")
        except Exception as e:
            return error_response(f"Error updating tooltip: {str(e)}", status_code=500)

    @staticmethod
    def delete(tooltip_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, element_name FROM tooltips WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (tooltip_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Tooltip not found", status_code=404)
                
            name = existing["result"]["element_name"]
            execute_query("DELETE FROM tooltips WHERE id = %s AND user_id = %s", (tooltip_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "TOOLTIPS", tooltip_id, f"Deleted tooltip for '{name}' (id: {tooltip_id})")
            
            return success_response(message="Tooltip deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting tooltip: {str(e)}", status_code=500)
