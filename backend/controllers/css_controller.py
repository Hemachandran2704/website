from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class CssController:
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
                where_clauses.append("(property_name LIKE %s OR property_value LIKE %s OR selector LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, property_name, property_value, selector, status,
                       created_at, updated_at
                FROM css_properties
                {where_sql}
                ORDER BY id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            return success_response(items, message="CSS properties retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching CSS properties: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(prop_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, property_name, property_value, selector, status,
                       created_at, updated_at
                FROM css_properties WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (prop_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("CSS property not found", status_code=404)
            return success_response(res["result"], message="CSS property retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching CSS property: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_css_property(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            property_name = data.get("property_name").strip().lower()
            property_value = data.get("property_value").strip()
            selector = data.get("selector").strip()
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO css_properties (user_id, property_name, property_value, selector, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, property_name, property_value, selector, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "CSS_PROPERTIES", new_id, f"Created CSS rule '{selector} {{ {property_name}: {property_value}; }}'")
            
            return success_response({
                "id": new_id,
                "property_name": property_name,
                "property_value": property_value,
                "selector": selector
            }, message="CSS property created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating CSS property: {str(e)}", status_code=500)

    @staticmethod
    def update(prop_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, property_name, selector FROM css_properties WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (prop_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("CSS property not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_css_property(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            property_name = data.get("property_name").strip().lower()
            property_value = data.get("property_value").strip()
            selector = data.get("selector").strip()
            status = data.get("status", "active")
            
            query = """
                UPDATE css_properties
                SET property_name = %s, property_value = %s, selector = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (property_name, property_value, selector, status, prop_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "CSS_PROPERTIES", prop_id, f"Updated CSS rule '{selector} {{ {property_name}: {property_value}; }}' (id: {prop_id})")
            
            return success_response({
                "id": prop_id,
                "property_name": property_name,
                "property_value": property_value,
                "selector": selector
            }, message="CSS property updated successfully")
        except Exception as e:
            return error_response(f"Error updating CSS property: {str(e)}", status_code=500)

    @staticmethod
    def delete(prop_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, property_name, selector FROM css_properties WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (prop_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("CSS property not found", status_code=404)
                
            prop_data = existing["result"]
            execute_query("DELETE FROM css_properties WHERE id = %s AND user_id = %s", (prop_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "CSS_PROPERTIES", prop_id, f"Deleted CSS property '{prop_data['property_name']}' on '{prop_data['selector']}' (id: {prop_id})")
            
            return success_response(message="CSS property deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting CSS property: {str(e)}", status_code=500)
