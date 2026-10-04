from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class SliderController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            slider_scope, params = readable_owner_scope(user, "s")
            image_scope, image_params = readable_owner_scope(user, "i")
            where_clauses = [slider_scope, image_scope]
            params.extend(image_params)
            
            if not user or status_param == "active":
                where_clauses.append("s.status = %s")
                params.append("active")
            elif status_param == "inactive":
                where_clauses.append("s.status = %s")
                params.append("inactive")
                
            if search:
                where_clauses.append("(s.title LIKE %s OR s.description LIKE %s OR i.title LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT s.id, s.user_id, s.title, s.description, s.image_id, s.display_order, s.status,
                       i.file_path, i.alt_text, i.title as image_title,
                       s.created_at, s.updated_at
                FROM sliders s
                JOIN images i ON s.image_id = i.id
                {where_sql}
                ORDER BY s.display_order ASC, s.id ASC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            for item in items:
                item["image_url"] = f"/uploads/{item['file_path']}"
                
            return success_response(items, message="Sliders retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching sliders: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(slider_id):
        try:
            user = getattr(g, "current_user", None)
            slider_scope, owner_params = readable_owner_scope(user, "s")
            image_scope, image_params = readable_owner_scope(user, "i")
            query = """
                SELECT s.id, s.title, s.description, s.image_id, s.display_order, s.status,
                       i.file_path, i.alt_text, i.title as image_title,
                       s.created_at, s.updated_at
                FROM sliders s
                JOIN images i ON s.image_id = i.id
                WHERE s.id = %s AND """ + slider_scope + " AND " + image_scope + " LIMIT 1"
            res = execute_query(query, (slider_id, *owner_params, *image_params), fetch_one=True)
            if not res["result"]:
                return error_response("Slider not found", status_code=404)
            slide = res["result"]
            slide["image_url"] = f"/uploads/{slide['file_path']}"
            return success_response(slide, message="Slider retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching slider: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_slider(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            image_id = int(data.get("image_id"))
            user = g.current_user
            user_id = user["id"]
            image_scope, image_params = readable_owner_scope(user)
            img_chk = execute_query(
                "SELECT id FROM images WHERE id = %s AND " + image_scope,
                (image_id, *image_params), fetch_one=True
            )
            if not img_chk["result"]:
                return error_response("Referenced image does not exist.", status_code=400)
                
            title = data.get("title").strip()
            description = (data.get("description") or "").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                INSERT INTO sliders (user_id, title, description, image_id, display_order, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, description, image_id, display_order, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "SLIDERS", new_id, f"Created slider slide '{title}'")
            
            return success_response({"id": new_id, "title": title}, message="Slider slide created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating slider: {str(e)}", status_code=500)

    @staticmethod
    def update(slider_id):
        try:
            user = g.current_user
            user_id = user["id"]
            owner_clause, owner_params = editable_owner_scope(user)
            check_q = "SELECT id, title FROM sliders WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (slider_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Slider not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_slider(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            image_id = int(data.get("image_id"))
            image_scope, image_params = readable_owner_scope(user)
            img_chk = execute_query(
                "SELECT id FROM images WHERE id = %s AND " + image_scope,
                (image_id, *image_params), fetch_one=True
            )
            if not img_chk["result"]:
                return error_response("Referenced image does not exist.", status_code=400)
                
            title = data.get("title").strip()
            description = (data.get("description") or "").strip()
            display_order = int(data.get("display_order", 0))
            status = data.get("status", "active")
            
            query = """
                UPDATE sliders
                SET title = %s, description = %s, image_id = %s, display_order = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title, description, image_id, display_order, status, slider_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "SLIDERS", slider_id, f"Updated slider slide '{title}' (id: {slider_id})")
            
            return success_response({"id": slider_id, "title": title}, message="Slider updated successfully")
        except Exception as e:
            return error_response(f"Error updating slider: {str(e)}", status_code=500)

    @staticmethod
    def delete(slider_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title FROM sliders WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (slider_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Slider not found", status_code=404)
                
            title = existing["result"]["title"]
            execute_query("DELETE FROM sliders WHERE id = %s AND user_id = %s", (slider_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "SLIDERS", slider_id, f"Deleted slider '{title}' (id: {slider_id})")
            
            return success_response(message="Slider deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting slider: {str(e)}", status_code=500)
