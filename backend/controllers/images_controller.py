import os
from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.upload_service import UploadService
from backend.services.validation_service import ValidationService
from backend.services.ownership_service import editable_owner_scope, mark_manageable, readable_owner_scope
from backend.utils.responses import success_response, error_response


class ImagesController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            category = request.args.get("category", "").strip()
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
                
            if category:
                where_clauses.append("category = %s")
                params.append(category)
                
            if search:
                where_clauses.append("(title LIKE %s OR description LIKE %s OR alt_text LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, user_id, title, description, file_path, alt_text, category, status,
                       created_at, updated_at
                FROM images
                {where_sql}
                ORDER BY id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            items = mark_manageable(res["result"] or [], user)
            
            # Format static image URL
            for item in items:
                item["image_url"] = f"/uploads/{item['file_path']}"
                
            return success_response(items, message="Images retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching images: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(image_id):
        try:
            user = getattr(g, "current_user", None)
            owner_clause, owner_params = readable_owner_scope(user)
            query = """
                SELECT id, title, description, file_path, alt_text, category, status,
                       created_at, updated_at
                FROM images WHERE id = %s AND """ + owner_clause + " LIMIT 1"
            res = execute_query(query, (image_id, *owner_params), fetch_one=True)
            if not res["result"]:
                return error_response("Image not found", status_code=404)
            img = res["result"]
            img["image_url"] = f"/uploads/{img['file_path']}"
            return success_response(img, message="Image retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching image: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            # Check for multipart/form-data or json
            title = request.form.get("title", "").strip()
            description = (request.form.get("description") or "").strip()
            alt_text = (request.form.get("alt_text") or "").strip()
            category = (request.form.get("category") or "General").strip()
            status = request.form.get("status", "active")
            
            is_valid, errors = ValidationService.validate_image_metadata({
                "title": title,
                "status": status
            })
            
            file = request.files.get("image_file")
            if not file or file.filename == "":
                errors["image_file"] = "Image file is required."
                
            if errors:
                return error_response("Validation failed", errors=errors, status_code=400)

            user_id = g.current_user["id"]
                
            filename, upload_err = UploadService.save_image(file)
            if upload_err:
                return error_response(upload_err, status_code=400)
                
            query = """
                INSERT INTO images (user_id, title, description, file_path, alt_text, category, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            res = execute_query(query, (user_id, title, description, filename, alt_text, category, status), commit=True)
            new_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "IMAGES", new_id, f"Uploaded image '{title}' ({filename})")
            
            return success_response({
                "id": new_id,
                "title": title,
                "file_path": filename,
                "image_url": f"/uploads/{filename}"
            }, message="Image uploaded successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error uploading image: {str(e)}", status_code=500)

    @staticmethod
    def update(image_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title, file_path FROM images WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (image_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Image not found", status_code=404)
                
            curr_file = existing["result"]["file_path"]
            
            # Form data can handle both json and multipart
            title = request.form.get("title") or (request.get_json(silent=True) or {}).get("title", "")
            description = request.form.get("description") or (request.get_json(silent=True) or {}).get("description", "")
            alt_text = request.form.get("alt_text") or (request.get_json(silent=True) or {}).get("alt_text", "")
            category = request.form.get("category") or (request.get_json(silent=True) or {}).get("category", "")
            status = request.form.get("status") or (request.get_json(silent=True) or {}).get("status", "active")
            
            is_valid, errors = ValidationService.validate_image_metadata({
                "title": title,
                "status": status
            }, is_update=True)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            # Check if replacement image file was uploaded
            new_filename = curr_file
            if "image_file" in request.files:
                file = request.files.get("image_file")
                if file and file.filename != "":
                    saved_name, upload_err = UploadService.save_image(file)
                    if upload_err:
                        return error_response(upload_err, status_code=400)
                    new_filename = saved_name
                    # Optionally delete old file
                    UploadService.delete_image_file(curr_file)
                    
            query = """
                UPDATE images
                SET title = %s, description = %s, file_path = %s, alt_text = %s, category = %s, status = %s
                WHERE id = %s AND user_id = %s
            """
            execute_query(query, (title.strip(), description.strip(), new_filename, alt_text.strip(), category.strip(), status, image_id, user_id), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "IMAGES", image_id, f"Updated image metadata '{title}' (id: {image_id})")
            
            return success_response({
                "id": image_id,
                "title": title,
                "file_path": new_filename,
                "image_url": f"/uploads/{new_filename}"
            }, message="Image updated successfully")
        except Exception as e:
            return error_response(f"Error updating image: {str(e)}", status_code=500)

    @staticmethod
    def delete(image_id):
        try:
            user_id = g.current_user["id"]
            owner_clause, owner_params = editable_owner_scope(g.current_user)
            check_q = "SELECT id, title, file_path FROM images WHERE id = %s AND " + owner_clause
            existing = execute_query(check_q, (image_id, *owner_params), fetch_one=True)
            if not existing["result"]:
                return error_response("Image not found", status_code=404)
                
            img_data = existing["result"]
            
            # Delete record (foreign keys cascade or restrict sliders)
            execute_query("DELETE FROM images WHERE id = %s AND user_id = %s", (image_id, user_id), commit=True)
            UploadService.delete_image_file(img_data["file_path"])
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "IMAGES", image_id, f"Deleted image '{img_data['title']}' (id: {image_id})")
            
            return success_response(message="Image deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting image: {str(e)}", status_code=500)
