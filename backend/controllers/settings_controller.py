from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.utils.responses import success_response, error_response
from backend.utils.validators import sanitize_input


class SettingsController:
    @staticmethod
    def get_user_settings():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            res = execute_query("SELECT * FROM user_settings WHERE user_id = %s", (curr_user["id"],), fetch_one=True)
            if not res["result"]:
                # Insert defaults
                execute_query("INSERT INTO user_settings (user_id) VALUES (%s)", (curr_user["id"],), commit=True)
                res = execute_query("SELECT * FROM user_settings WHERE user_id = %s", (curr_user["id"],), fetch_one=True)

            return success_response(res["result"] or {}, message="User settings retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch user settings: {str(e)}", status_code=500)

    @staticmethod
    def update_user_settings():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            email_notifs = 1 if data.get("email_notifications", True) else 0
            sec_alerts = 1 if data.get("security_alerts", True) else 0
            act_digest = 1 if data.get("activity_digest", True) else 0
            lang = sanitize_input(data.get("language") or "en")
            appearance = sanitize_input(data.get("appearance") or "light")
            phone = sanitize_input(data.get("phone") or "")
            department = sanitize_input(data.get("department") or "")
            bio = sanitize_input(data.get("bio") or "")

            set_res = execute_query("SELECT id FROM user_settings WHERE user_id = %s", (curr_user["id"],), fetch_one=True)
            if set_res["result"]:
                query = """
                    UPDATE user_settings
                    SET email_notifications = %s, security_alerts = %s, activity_digest = %s,
                        language = %s, appearance = %s, phone = %s, department = %s, bio = %s
                    WHERE user_id = %s
                """
                execute_query(query, (email_notifs, sec_alerts, act_digest, lang, appearance, phone, department, bio, curr_user["id"]), commit=True)
            else:
                query = """
                    INSERT INTO user_settings (user_id, email_notifications, security_alerts, activity_digest, language, appearance, phone, department, bio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(query, (curr_user["id"], email_notifs, sec_alerts, act_digest, lang, appearance, phone, department, bio), commit=True)

            log_audit(curr_user["id"], "UPDATE_SETTINGS", "SETTINGS", curr_user["id"], "User updated personal settings")
            return success_response(message="Preferences saved successfully")
        except Exception as e:
            return error_response(f"Failed to save settings: {str(e)}", status_code=500)

    @staticmethod
    def get_system_settings():
        """
        Admin only: fetch system-wide configurations.
        """
        try:
            res = execute_query("SELECT * FROM system_settings ORDER BY id ASC", fetch_all=True)
            settings_list = res["result"] or []
            settings_map = {s["setting_key"]: s["setting_value"] for s in settings_list}
            return success_response({"items": settings_list, "map": settings_map}, message="System settings retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch system settings: {str(e)}", status_code=500)

    @staticmethod
    def update_system_settings():
        """
        Admin only: update system-wide configurations.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            data = request.get_json(silent=True) or {}

            for key, val in data.items():
                sanitized_val = sanitize_input(str(val))
                execute_query("""
                    INSERT INTO system_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = %s
                """, (key, sanitized_val, sanitized_val), commit=True)

            log_audit(curr_user["id"] if curr_user else None, "UPDATE_SYSTEM_SETTINGS", "SETTINGS", None, "Admin updated system configurations")
            return success_response(message="System settings updated successfully")
        except Exception as e:
            # Fallback for MySQL if ON CONFLICT syntax differs
            try:
                for key, val in data.items():
                    sanitized_val = sanitize_input(str(val))
                    ex = execute_query("SELECT id FROM system_settings WHERE setting_key = %s", (key,), fetch_one=True)
                    if ex["result"]:
                        execute_query("UPDATE system_settings SET setting_value = %s WHERE setting_key = %s", (sanitized_val, key), commit=True)
                    else:
                        execute_query("INSERT INTO system_settings (setting_key, setting_value) VALUES (%s, %s)", (key, sanitized_val), commit=True)
                return success_response(message="System settings updated successfully")
            except Exception as e2:
                return error_response(f"Failed to update system settings: {str(e2)}", status_code=500)
