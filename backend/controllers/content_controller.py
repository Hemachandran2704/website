from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.utils.responses import success_response, error_response


class ContentController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            category_param = request.args.get("category", "").strip()
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            is_admin = user and user.get("role") == "admin"
            
            where_clauses = []
            params = []
            
            if not is_admin or status_param == "active":
                where_clauses.append("status = %s")
                params.append("active")
            elif status_param == "inactive":
                where_clauses.append("status = %s")
                params.append("inactive")
                
            if category_param and category_param.lower() != "all":
                where_clauses.append("category = %s")
                params.append(category_param)
                
            if search:
                where_clauses.append("(title LIKE %s OR description LIKE %s OR content LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, title, description, content, category, display_order, status,
                       created_at, updated_at
                FROM content_manager
                {where_sql}
                ORDER BY display_order ASC, id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            return success_response(res["result"] or [], message="Content records retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching content: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(content_id):
        try:
            query = """
                SELECT id, title, description, content, category, display_order, status,
                       created_at, updated_at
                FROM content_manager WHERE id = %s LIMIT 1
            """
            res = execute_query(query, (content_id,), fetch_one=True)
            if not res["result"]:
                return error_response("Content not found", status_code=404)
            return success_response(res["result"], message="Content retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching content item: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_content(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            description = data.get("description", "").strip() or None
            content = data.get("content").strip()
            category = data.get("category", "General").strip() or "General"
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                INSERT INTO content_manager (title, description, content, category, display_order, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (title, description, content, category, display_order, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "CONTENT", new_id, f"Created content '{title}'")
            
            return success_response({"id": new_id, "title": title}, message="Content created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating content: {str(e)}", status_code=500)

    @staticmethod
    def update(content_id):
        try:
            check_q = "SELECT id, title FROM content_manager WHERE id = %s"
            existing = execute_query(check_q, (content_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Content not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_content(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            description = data.get("description", "").strip() or None
            content = data.get("content").strip()
            category = data.get("category", "General").strip() or "General"
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                UPDATE content_manager
                SET title = %s, description = %s, content = %s, category = %s, display_order = %s, status = %s
                WHERE id = %s
            """
            execute_query(query, (title, description, content, category, display_order, status, content_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "CONTENT", content_id, f"Updated content '{title}' (id: {content_id})")
            
            return success_response({"id": content_id, "title": title, "status": status}, message="Content updated successfully")
        except Exception as e:
            return error_response(f"Error updating content: {str(e)}", status_code=500)

    @staticmethod
    def delete(content_id):
        try:
            check_q = "SELECT id, title FROM content_manager WHERE id = %s"
            existing = execute_query(check_q, (content_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Content not found", status_code=404)
                
            content_title = existing["result"]["title"]
            delete_q = "DELETE FROM content_manager WHERE id = %s"
            execute_query(delete_q, (content_id,), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "CONTENT", content_id, f"Deleted content '{content_title}' (id: {content_id})")
            
            return success_response(message="Content deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting content: {str(e)}", status_code=500)
