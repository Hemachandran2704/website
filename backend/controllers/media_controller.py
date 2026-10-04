import os
from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.upload_service import UploadService
from backend.services.validation_service import ValidationService
from backend.utils.responses import success_response, error_response


class MediaController:
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
                where_clauses.append("(file_name LIKE %s OR description LIKE %s OR category LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, file_name, file_type, file_path, description, category, status,
                       created_at, updated_at
                FROM media_manager
                {where_sql}
                ORDER BY id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            items = res["result"] or []
            
            # Format image url
            for item in items:
                item["url"] = f"/uploads/{item['file_path']}"
                
            return success_response(items, message="Media items retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching media: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(media_id):
        try:
            query = """
                SELECT id, file_name, file_type, file_path, description, category, status,
                       created_at, updated_at
                FROM media_manager WHERE id = %s LIMIT 1
            """
            res = execute_query(query, (media_id,), fetch_one=True)
            if not res["result"]:
                return error_response("Media item not found", status_code=404)
            data = res["result"]
            data["url"] = f"/uploads/{data['file_path']}"
            return success_response(data, message="Media retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching media item: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            # Handle multipart/form-data or json
            file_obj = request.files.get("media_file") or request.files.get("file")
            file_path = None
            file_name = None
            file_type = "image/png"
            
            if file_obj:
                saved_name, err = UploadService.save_media(file_obj)
                if err:
                    return error_response(err, status_code=400)
                file_path = saved_name
                file_name = file_obj.filename
                file_type = file_obj.content_type or "application/octet-stream"
            else:
                data = request.get_json(silent=True) or request.form or {}
                file_path = data.get("file_path") or "sample_cloud.webp"
                file_name = data.get("file_name") or "media_upload.png"
                file_type = data.get("file_type") or "image/png"
                
            data = request.form if request.form else (request.get_json(silent=True) or {})
            if not file_name:
                file_name = data.get("file_name", "uploaded_file.png")
                
            description = data.get("description", "").strip() or None
            category = data.get("category", "General").strip() or "General"
            status = data.get("status", "active")
            
            query = """
                INSERT INTO media_manager (file_name, file_type, file_path, description, category, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (file_name, file_type, file_path, description, category, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "MEDIA", new_id, f"Uploaded media '{file_name}'")
            
            return success_response({
                "id": new_id,
                "file_name": file_name,
                "file_path": file_path,
                "url": f"/uploads/{file_path}"
            }, message="Media uploaded successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating media: {str(e)}", status_code=500)

    @staticmethod
    def update(media_id):
        try:
            check_q = "SELECT id, file_name, file_path, file_type FROM media_manager WHERE id = %s"
            existing = execute_query(check_q, (media_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Media item not found", status_code=404)
                
            file_obj = request.files.get("media_file") or request.files.get("file")
            file_path = existing["result"]["file_path"]
            file_name = existing["result"]["file_name"]
            file_type = existing["result"]["file_type"]
            
            if file_obj:
                saved_name, err = UploadService.save_media(file_obj)
                if err:
                    return error_response(err, status_code=400)
                file_path = saved_name
                file_name = file_obj.filename
                file_type = file_obj.content_type or "application/octet-stream"
                
            data = request.form if request.form else (request.get_json(silent=True) or {})
            if "file_name" in data and data.get("file_name"):
                file_name = data.get("file_name").strip()
                
            description = data.get("description", "").strip() or None
            category = data.get("category", "General").strip() or "General"
            status = data.get("status", "active")
            
            query = """
                UPDATE media_manager
                SET file_name = %s, file_type = %s, file_path = %s, description = %s, category = %s, status = %s
                WHERE id = %s
            """
            execute_query(query, (file_name, file_type, file_path, description, category, status, media_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "MEDIA", media_id, f"Updated media metadata for '{file_name}' (id: {media_id})")
            
            return success_response({"id": media_id, "file_name": file_name, "file_path": file_path, "url": f"/uploads/{file_path}"}, message="Media updated successfully")
        except Exception as e:
            return error_response(f"Error updating media: {str(e)}", status_code=500)

    @staticmethod
    def delete(media_id):
        try:
            check_q = "SELECT id, file_name, file_path FROM media_manager WHERE id = %s"
            existing = execute_query(check_q, (media_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Media item not found", status_code=404)
                
            item = existing["result"]
            file_name = item["file_name"]
            
            delete_q = "DELETE FROM media_manager WHERE id = %s"
            execute_query(delete_q, (media_id,), commit=True)
            
            # Delete physical file
            UploadService.delete_image_file(item.get("file_path"))
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "MEDIA", media_id, f"Deleted media '{file_name}' (id: {media_id})")
            
            return success_response(message="Media deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting media: {str(e)}", status_code=500)
