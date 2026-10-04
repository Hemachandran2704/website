from flask import request, g
from backend.config.database import execute_query
from backend.utils.responses import success_response, error_response
from backend.utils.validators import sanitize_input


class FavoriteController:
    @staticmethod
    def get_favorites():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            res = execute_query("SELECT * FROM user_favorites WHERE user_id = %s ORDER BY id DESC", (curr_user["id"],), fetch_all=True)
            return success_response(res["result"] or [], message="Favorites retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch favorites: {str(e)}", status_code=500)

    @staticmethod
    def add_favorite():
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            title = sanitize_input(data.get("title") or "")
            url = sanitize_input(data.get("url") or "")
            category = sanitize_input(data.get("category") or "Module")

            if not title or not url:
                return error_response("Title and URL are required", status_code=400)

            query = """
                INSERT INTO user_favorites (user_id, title, url, category)
                VALUES (%s, %s, %s, %s)
            """
            res = execute_query(query, (curr_user["id"], title, url, category), commit=True)
            return success_response({"id": res["last_id"], "title": title}, message="Added to favorites", status_code=201)
        except Exception as e:
            return error_response(f"Failed to add favorite: {str(e)}", status_code=500)

    @staticmethod
    def delete_favorite(fav_id):
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            execute_query("DELETE FROM user_favorites WHERE id = %s AND user_id = %s", (fav_id, curr_user["id"]), commit=True)
            return success_response(message="Removed from favorites")
        except Exception as e:
            return error_response(f"Failed to delete favorite: {str(e)}", status_code=500)
