from flask import request, g
from backend.config.database import execute_query
from backend.utils.responses import success_response, error_response
from backend.utils.validators import sanitize_input


class ScheduleController:
    @staticmethod
    def get_schedules():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            res = execute_query("SELECT * FROM user_schedules WHERE user_id = %s ORDER BY event_date ASC, event_time ASC", (curr_user["id"],), fetch_all=True)
            return success_response(res["result"] or [], message="Schedule events retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch schedules: {str(e)}", status_code=500)

    @staticmethod
    def create_schedule():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            title = sanitize_input(data.get("title") or "")
            description = sanitize_input(data.get("description") or "")
            event_date = sanitize_input(data.get("event_date") or "")
            event_time = sanitize_input(data.get("event_time") or "09:00")

            if not title or not event_date:
                return error_response("Title and event date are required", status_code=400)

            query = """
                INSERT INTO user_schedules (user_id, title, description, event_date, event_time, status)
                VALUES (%s, %s, %s, %s, %s, 'upcoming')
            """
            res = execute_query(query, (curr_user["id"], title, description, event_date, event_time), commit=True)
            return success_response({"id": res["last_id"], "title": title}, message="Event added to calendar", status_code=201)
        except Exception as e:
            return error_response(f"Failed to add schedule: {str(e)}", status_code=500)

    @staticmethod
    def delete_schedule(schedule_id):
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            execute_query("DELETE FROM user_schedules WHERE id = %s AND user_id = %s", (schedule_id, curr_user["id"]), commit=True)
            return success_response(message="Schedule event deleted")
        except Exception as e:
            return error_response(f"Failed to delete schedule: {str(e)}", status_code=500)
