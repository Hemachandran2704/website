import json
from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.services.validation_service import ValidationService
from backend.utils.responses import success_response, error_response


class FormController:
    @staticmethod
    def get_all():
        try:
            status_param = request.args.get("status", "").strip().lower()
            search = request.args.get("search", "").strip()
            
            user = getattr(g, "current_user", None)
            is_admin = user and user.get("role") == "admin"
            
            where_clauses = []
            params = []
            
            if not is_admin or status_param == "active":
                where_clauses.append("f.status = %s")
                params.append("active")
            elif status_param == "inactive":
                where_clauses.append("f.status = %s")
                params.append("inactive")
                
            if search:
                where_clauses.append("(f.title LIKE %s OR f.description LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT f.id, f.title, f.description, f.status, f.created_at, f.updated_at,
                       (SELECT COUNT(*) FROM form_fields ff WHERE ff.form_id = f.id) AS field_count,
                       (SELECT COUNT(*) FROM form_submissions fs WHERE fs.form_id = f.id) AS submission_count
                FROM forms f
                {where_sql}
                ORDER BY f.id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            return success_response(res["result"] or [], message="Forms retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching forms: {str(e)}", status_code=500)

    @staticmethod
    def get_by_id(form_id):
        try:
            query = """
                SELECT id, title, description, status, created_at, updated_at
                FROM forms WHERE id = %s LIMIT 1
            """
            res = execute_query(query, (form_id,), fetch_one=True)
            if not res["result"]:
                return error_response("Form not found", status_code=404)
                
            form_data = res["result"]
            
            # Fetch fields
            fields_q = """
                SELECT id, form_id, field_label, field_name, field_type, options, is_required, display_order
                FROM form_fields
                WHERE form_id = %s
                ORDER BY display_order ASC, id ASC
            """
            fields_res = execute_query(fields_q, (form_id,), fetch_all=True)
            form_data["fields"] = fields_res["result"] or []
            
            return success_response(form_data, message="Form retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching form: {str(e)}", status_code=500)

    @staticmethod
    def create():
        try:
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_form(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            description = data.get("description", "").strip() or None
            status = data.get("status", "active")
            fields = data.get("fields", [])
            
            query = """
                INSERT INTO forms (title, description, status)
                VALUES (%s, %s, %s)
            """
            res = execute_query(query, (title, description, status), commit=True)
            form_id = res["last_id"]
            
            # Insert fields if provided
            if fields and isinstance(fields, list):
                for idx, fld in enumerate(fields):
                    f_label = fld.get("field_label", "").strip()
                    f_name = fld.get("field_name", f_label.lower().replace(" ", "_")).strip()
                    f_type = fld.get("field_type", "text").strip().lower()
                    f_options = fld.get("options", "").strip()
                    f_required = 1 if fld.get("is_required") else 0
                    f_order = int(fld.get("display_order", idx + 1))
                    
                    if f_label and f_name:
                        fq = """
                            INSERT INTO form_fields (form_id, field_label, field_name, field_type, options, is_required, display_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        execute_query(fq, (form_id, f_label, f_name, f_type, f_options, f_required, f_order), commit=True)
                        
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "CREATE", "FORMS", form_id, f"Created form '{title}'")
            
            return success_response({"id": form_id, "title": title}, message="Form created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Error creating form: {str(e)}", status_code=500)

    @staticmethod
    def update(form_id):
        try:
            check_q = "SELECT id, title FROM forms WHERE id = %s"
            existing = execute_query(check_q, (form_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Form not found", status_code=404)
                
            data = request.get_json(silent=True) or {}
            is_valid, errors = ValidationService.validate_form(data)
            if not is_valid:
                return error_response("Validation failed", errors=errors, status_code=400)
                
            title = data.get("title").strip()
            description = data.get("description", "").strip() or None
            status = data.get("status", "active")
            fields = data.get("fields", None)
            
            query = """
                UPDATE forms
                SET title = %s, description = %s, status = %s
                WHERE id = %s
            """
            execute_query(query, (title, description, status, form_id), commit=True)
            
            # If fields list provided, update fields
            if fields is not None and isinstance(fields, list):
                # Delete existing fields
                execute_query("DELETE FROM form_fields WHERE form_id = %s", (form_id,), commit=True)
                for idx, fld in enumerate(fields):
                    f_label = fld.get("field_label", "").strip()
                    f_name = fld.get("field_name", f_label.lower().replace(" ", "_")).strip()
                    f_type = fld.get("field_type", "text").strip().lower()
                    f_options = fld.get("options", "").strip()
                    f_required = 1 if fld.get("is_required") else 0
                    f_order = int(fld.get("display_order", idx + 1))
                    
                    if f_label and f_name:
                        fq = """
                            INSERT INTO form_fields (form_id, field_label, field_name, field_type, options, is_required, display_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        execute_query(fq, (form_id, f_label, f_name, f_type, f_options, f_required, f_order), commit=True)
                        
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "UPDATE", "FORMS", form_id, f"Updated form '{title}' (id: {form_id})")
            
            return success_response({"id": form_id, "title": title}, message="Form updated successfully")
        except Exception as e:
            return error_response(f"Error updating form: {str(e)}", status_code=500)

    @staticmethod
    def delete(form_id):
        try:
            check_q = "SELECT id, title FROM forms WHERE id = %s"
            existing = execute_query(check_q, (form_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Form not found", status_code=404)
                
            form_title = existing["result"]["title"]
            delete_q = "DELETE FROM forms WHERE id = %s"
            execute_query(delete_q, (form_id,), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "FORMS", form_id, f"Deleted form '{form_title}' (id: {form_id})")
            
            return success_response(message="Form deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting form: {str(e)}", status_code=500)

    # Submissions
    @staticmethod
    def submit_form(form_id):
        try:
            check_q = "SELECT id, title, status FROM forms WHERE id = %s"
            existing = execute_query(check_q, (form_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Form not found", status_code=404)
            if existing["result"]["status"] != "active":
                return error_response("This form is currently inactive and not accepting submissions.", status_code=400)
                
            data = request.get_json(silent=True) or request.form.to_dict() or {}
            ip_addr = request.remote_addr or "127.0.0.1"
            
            # Serialize submitted data
            json_str = json.dumps(data)
            
            query = """
                INSERT INTO form_submissions (form_id, submitted_data, ip_address)
                VALUES (%s, %s, %s)
            """
            res = execute_query(query, (form_id, json_str, ip_addr), commit=True)
            sub_id = res["last_id"]
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "SUBMIT", "FORMS", form_id, f"Form submission #{sub_id} received for '{existing['result']['title']}'")
            
            return success_response({"id": sub_id, "submission_id": sub_id}, message="Form submitted successfully! Thank you.", status_code=201)
        except Exception as e:
            return error_response(f"Error submitting form: {str(e)}", status_code=500)

    @staticmethod
    def get_submissions(form_id=None):
        try:
            where_sql = ""
            params = []
            if form_id:
                where_sql = "WHERE fs.form_id = %s"
                params.append(form_id)
                
            search = request.args.get("search", "").strip()
            if search:
                clause = "(fs.submitted_data LIKE %s OR f.title LIKE %s)"
                if where_sql:
                    where_sql += f" AND {clause}"
                else:
                    where_sql = f"WHERE {clause}"
                params.extend([f"%{search}%", f"%{search}%"])
                
            query = f"""
                SELECT fs.id, fs.form_id, fs.submitted_data, fs.ip_address, fs.created_at,
                       f.title AS form_title
                FROM form_submissions fs
                JOIN forms f ON fs.form_id = f.id
                {where_sql}
                ORDER BY fs.id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            raw_items = res["result"] or []
            
            items = []
            for item in raw_items:
                parsed = {}
                try:
                    parsed = json.loads(item["submitted_data"])
                except Exception:
                    parsed = {"raw": item["submitted_data"]}
                item["parsed_data"] = parsed
                items.append(item)
                
            return success_response(items, message="Form submissions retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching form submissions: {str(e)}", status_code=500)

    @staticmethod
    def delete_submission(sub_id):
        try:
            check_q = "SELECT id, form_id FROM form_submissions WHERE id = %s"
            existing = execute_query(check_q, (sub_id,), fetch_one=True)
            if not existing["result"]:
                return error_response("Submission not found", status_code=404)
                
            delete_q = "DELETE FROM form_submissions WHERE id = %s"
            execute_query(delete_q, (sub_id,), commit=True)
            
            user = getattr(g, "current_user", None)
            user_id = user["id"] if user else None
            log_audit(user_id, "DELETE", "FORMS", sub_id, f"Deleted form submission #{sub_id}")
            
            return success_response(message="Form submission deleted successfully")
        except Exception as e:
            return error_response(f"Error deleting submission: {str(e)}", status_code=500)
