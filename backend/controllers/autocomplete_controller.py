from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class AutocompleteController:
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
                where_clauses.append("(label LIKE %s OR value LIKE %s OR description LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, label, value, description, status,
                       created_at, updated_at
                FROM autocomplete_items
                {where_sql}
                ORDER BY label ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="Autocomplete items retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching items: {str(e)}", status_code=500)

    @staticmethod
    def search():
        """
        Dynamic search endpoint matching at least 2 characters.
        Uses SQL LIKE with parameterized queries.
        """
        try:
            q = request.args.get("q", "").strip()
            if len(q) < 2:
                return success_response([], message="Query must contain at least 2 characters")
                
            # By default only active items for search suggestions
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = f"""
                SELECT id, label, value, description, status
                FROM autocomplete_items
                WHERE status = 'active' AND {owner_clause}
                  AND (label LIKE %s OR value LIKE %s OR description LIKE %s)
                ORDER BY label ASC
                LIMIT 10
            """
            pattern = f"%{q}%"
            res = execute_query(query, (*owner_params, pattern, pattern, pattern), fetch_all=True)
            return success_response(res["result"] or [], message="Search suggestions found")
        except Exception as e:
            return error_response(f"Error searching autocomplete: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(item_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, label, value, description, status,
                       created_at, updated_at
                FROM autocomplete_items WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (item_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Item not found", status_code=404)
            return success_response(res["result"], message="Item retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching item: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_autocomplete(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            label = data.get("label").strip()
            value = data.get("value").strip()
            description = (data.get("description") or "").strip()
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO autocomplete_items (user_id, label, value, description, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, label, value, description, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "AUTOCOMPLETE", new_id, f"Created autocomplete item '{label}'")
            
            return success_response({"id": new_id, "label": label}, message="Item created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating item: {str(e)}", status_code=500)

    @staticmethod
    def update(item_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, label FROM autocomplete_items WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (item_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Item not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_autocomplete(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            label = data.get("label").strip()
            value = data.get("value").strip()
            description = (data.get("description") or "").strip()
            status = data.get("status", "active")
            
            query = """
                UPDATE autocomplete_items
                SET label = %s, value = %s, description = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (label, value, description, status, item_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "AUTOCOMPLETE", item_id, f"Updated autocomplete item '{label}' (id: {item_id})")
            
            return success_response({"id": item_id, "label": label}, message="Item updated successfully")
        except Exception as e:
            return error_response(f"Error updating item: {str(e)}", status_code=500)

    @staticmethod
    def delete(item_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, label FROM autocomplete_items WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (item_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Item not found", status_code=404)
                
            label = existing["result"]["label"]
            execute_query("DELETE FROM autocomplete_items WHERE id = %s AND user_id = %s", (item_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "AUTOCOMPLETE", item_id, f"Deleted autocomplete item '{label}' (id: {item_id})")
            
            return success_response(message="Item deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting item: {str(e)}", status_code=500)
