from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import mark_manageable
from backend.utils.responses import success_response, error_response


class TabsController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            search = request.args.get("search", "").strip()
            
            # If unauthenticated, only show active
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            is_authenticated = user_id is not None
            
            where_clauses = []
            params = []
            if is_authenticated:
                where_clauses.append("(user_id IS NULL OR user_id = %s)")
                params.append(user_id)
            else:
                where_clauses.append("user_id IS NULL")
            
            if not is_authenticated or status_param == "active":
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
                FROM tabs
                {where_sql}
                ORDER BY display_order ASC, id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            return success_response(mark_manageable(res["result"] or [], user), message="Tabs retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching tabs: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(tab_id):
        try:
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            owner_clause = "(user_id IS NULL OR user_id = %s)" if user_id is not None else "user_id IS NULL"
            query = """
                SELECT id, title, content, display_order, status,
                       created_at, updated_at
                FROM tabs WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            params = (tab_id, user_id) if user_id is not None else (tab_id,)
            res = execute_query(query, params, fetch_one=True)
            if not res["result"]:
                return error_response("Tab not found", status_code=404)
            return success_response(res["result"], message="Tab retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching tab: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_tab(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            user_id = g.current_user["id"]
            
            query = """
                INSERT INTO tabs (user_id, title, content, display_order, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, content, display_order, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "TABS", new_id, f"Created tab '{title}'")
            
            return success_response({"id": new_id, "title": title}, message="Tab created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating tab: {str(e)}", status_code=500)

    @staticmethod
    def update(tab_id):
        try:
            user_id = g.current_user["id"]
            check_q = "SELECT id, title FROM tabs WHERE id = %s AND user_id = %s"
            existing = execute_query(check_q, (tab_id, user_id), fetch_one=True)
            if not existing["result"]:
                return error_response("Tab not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_tab(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            content = data.get("content").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                UPDATE tabs
                SET title = %s, content = %s, display_order = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title, content, display_order, status, tab_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "TABS", tab_id, f"Updated tab '{title}' (id: {tab_id})")
            
            return success_response({"id": tab_id, "title": title}, message="Tab updated successfully")
        except Exception as e:
            return error_response(f"Error updating tab: {str(e)}", status_code=500)

    @staticmethod
    def delete(tab_id):
        try:
            user_id = g.current_user["id"]
            check_q = "SELECT id, title FROM tabs WHERE id = %s AND user_id = %s"
            existing = execute_query(check_q, (tab_id, user_id), fetch_one=True)
            if not existing["result"]:
                return error_response("Tab not found", status_code=404)
                
            tab_title = existing["result"]["title"]
            delete_q = "DELETE FROM tabs WHERE id = %s AND user_id = %s"
            execute_query(delete_q, (tab_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "TABS", tab_id, f"Deleted tab '{tab_title}' (id: {tab_id})")
            
            return success_response(message="Tab deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting tab: {str(e)}", status_code=500)
