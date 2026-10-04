from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class CollapsibleController:
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
                where_clauses.append("(title LIKE %s OR content LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, title, content, display_order, status,
                       created_at, updated_at
                FROM collapsible_contents
                {where_sql}
                ORDER BY display_order ASC, id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="Collapsible contents retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching collapsible contents: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(item_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, title, content, display_order, status,
                       created_at, updated_at
                FROM collapsible_contents WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (item_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Collapsible content not found", status_code=404)
            return success_response(res["result"], message="Collapsible content retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching collapsible content: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_collapsible(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO collapsible_contents (user_id, title, content, display_order, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, content, display_order, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "COLLAPSIBLE", new_id, f"Created collapsible content '{title}'")
            
            return success_response({"id": new_id, "title": title}, message="Collapsible content created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating collapsible content: {str(e)}", status_code=500)

    @staticmethod
    def update(item_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM collapsible_contents WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (item_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Collapsible content not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_collapsible(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                UPDATE collapsible_contents
                SET title = %s, content = %s, display_order = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title, content, display_order, status, item_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "COLLAPSIBLE", item_id, f"Updated collapsible content '{title}' (id: {item_id})")
            
            return success_response({"id": item_id, "title": title}, message="Collapsible content updated successfully")
        except Exception as e:
            return error_response(f"Error updating collapsible content: {str(e)}", status_code=500)

    @staticmethod
    def delete(item_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM collapsible_contents WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (item_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Collapsible content not found", status_code=404)
                
            title = existing["result"]["title"]
            execute_query("DELETE FROM collapsible_contents WHERE id = %s AND user_id = %s", (item_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "COLLAPSIBLE", item_id, f"Deleted collapsible content '{title}' (id: {item_id})")
            
            return success_response(message="Collapsible content deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting collapsible content: {str(e)}", status_code=500)
