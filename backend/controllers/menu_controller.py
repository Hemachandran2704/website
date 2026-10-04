from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class MenuController:
    @staticmethod
    def _build_tree(items, parent_id=None):
        tree = []
        for item in items:
            if item.get("parent_id") == parent_id:
                children = MenuController._build_tree(items, item["id"])
                item_copy = dict(item)
                item_copy["children"] = children
                tree.append(item_copy)
        return tree

    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            as_tree = request.args.get("tree", "").strip().lower() in ("true", "1")
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            owner_clause, params = readable_owner_scope(user, "m")
            where_clauses = [owner_clause]
            
            if not user or status_param == "active":
                where_clauses.append("m.status = %s")
                params.append("active")
            elif status_param == "inactive":
                where_clauses.append("m.status = %s")
                params.append("inactive")
                
            if search:
                where_clauses.append("m.name LIKE %s")
                params.append(f"%{search}%")
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT m.id, m.user_id, m.name, m.url, m.parent_id, m.display_order, m.status,
                       p.name as parent_name,
                       m.created_at, m.updated_at
                FROM menus m
                LEFT JOIN menus p ON m.parent_id = p.id
                {where_sql}
                ORDER BY m.parent_id ASC, m.display_order ASC, m.id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            
            if as_tree:
                tree_data = MenuController._build_tree(items, None)
                return success_response(tree_data, message="Menu tree retrieved successfully")
                
            return success_response(items, message="Menus retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching menus: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(menu_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user, "m")
            query = """
                SELECT m.id, m.name, m.url, m.parent_id, m.display_order, m.status,
                       p.name as parent_name,
                       m.created_at, m.updated_at
                FROM menus m
                LEFT JOIN menus p ON m.parent_id = p.id
                WHERE m.id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (menu_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Menu item not found", status_code=404)
            return success_response(res["result"], message="Menu item retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching menu item: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_menu(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            name = data.get("name").strip()
            url = data.get("url").strip()
            parent_id = data.get("parent_id")
            user = g.current_user
            user_id = user["id"]
            if parent_id in ("", None, "null", 0):
                parent_id = None
            else:
                parent_id = int(parent_id)
                # Verify parent exists
                parent_scope, parent_params = readable_owner_scope(user)
                p_check = execute_query(
                    "SELECT id FROM menus WHERE id = %s AND " + parent_scope,
                    (parent_id, *parent_params), fetch_one=True
                )
                if not p_check["result"]:
                    return error_response("Specified parent menu does not exist.", status_code=400)
                    
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                INSERT INTO menus (user_id, name, url, parent_id, display_order, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, name, url, parent_id, display_order, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "MENUS", new_id, f"Created menu item '{name}'")
            
            return success_response({"id": new_id, "name": name}, message="Menu item created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating menu item: {str(e)}", status_code=500)

    @staticmethod
    def update(menu_id):
        try:
            user = g.current_user
            user_id = user["id"]
            owner_clause, owner_params = editable_owner_scope(user)
            check_q = "SELECT id, name FROM menus WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (menu_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Menu item not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_menu(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            name = data.get("name").strip()
            url = data.get("url").strip()
            parent_id = data.get("parent_id")
            
            if parent_id in ("", None, "null", 0):
                parent_id = None
            else:
                parent_id = int(parent_id)
                if parent_id == int(menu_id):
                    return error_response("A menu item cannot be its own parent.", status_code=400)
                parent_scope, parent_params = readable_owner_scope(user)
                p_check = execute_query(
                    "SELECT id FROM menus WHERE id = %s AND " + parent_scope,
                    (parent_id, *parent_params), fetch_one=True
                )
                if not p_check["result"]:
                    return error_response("Specified parent menu does not exist.", status_code=400)
                    
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                UPDATE menus
                SET name = %s, url = %s, parent_id = %s, display_order = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (name, url, parent_id, display_order, status, menu_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "MENUS", menu_id, f"Updated menu item '{name}' (id: {menu_id})")
            
            return success_response({"id": menu_id, "name": name}, message="Menu item updated successfully")
        except Exception as e:
            return error_response(f"Error updating menu item: {str(e)}", status_code=500)

    @staticmethod
    def delete(menu_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, name FROM menus WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (menu_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Menu item not found", status_code=404)
                
            menu_name = existing["result"]["name"]
            
            # Reparent or nullify children parent_id
            execute_query("UPDATE menus SET parent_id = NULL WHERE parent_id = %s AND user_id = %s", (menu_id, user_id), commit=True)
            execute_query("DELETE FROM menus WHERE id = %s AND user_id = %s", (menu_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "MENUS", menu_id, f"Deleted menu item '{menu_name}' (id: {menu_id})")
            
            return success_response(message="Menu item deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting menu item: {str(e)}", status_code=500)
