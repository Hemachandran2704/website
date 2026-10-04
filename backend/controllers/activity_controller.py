from flask import request, g
from backend.config.database import execute_query
from backend.utils.responses import success_response, error_response


class ActivityController:
    @staticmethod
    def get_all():
        try:
            action_param = request.args.get("action", "").strip().upper()
            module_param = request.args.get("module", "").strip().upper()
            search = request.args.get("search", "").strip()
            
            # Pagination params
            try:
                page = max(1, int(request.args.get("page", 1)))
                limit = min(100, max(1, int(request.args.get("limit", 15))))
            except ValueError:
                page = 1
                limit = 15
            offset = (page - 1) * limit
            
            where_clauses = []
            params = []
            
            if action_param and action_param != "ALL":
                where_clauses.append("al.action = %s")
                params.append(action_param)
                
            if module_param and module_param != "ALL":
                where_clauses.append("al.module = %s")
                params.append(module_param)
                
            if search:
                where_clauses.append("(al.description LIKE %s OR al.module LIKE %s OR al.action LIKE %s OR u.name LIKE %s OR u.email LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
                
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # Get total count for pagination
            count_q = f"""
                SELECT COUNT(*) as total
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.id
                {where_sql}
            """
            count_res = execute_query(count_q, list(params), fetch_one=True)
            total = count_res["result"]["total"] if count_res["result"] else 0
            
            # Fetch paginated rows
            query = f"""
                SELECT al.id, al.user_id, al.action, al.module, al.record_id, al.description, al.created_at,
                       COALESCE(u.name, 'System') AS user_name,
                       u.email AS user_email,
                       u.role AS user_role
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.id
                {where_sql}
                ORDER BY al.id DESC
                LIMIT %s OFFSET %s
            """
            fetch_params = list(params) + [limit, offset]
            res = execute_query(query, fetch_params, fetch_all=True)
            
            total_pages = (total + limit - 1) // limit if total > 0 else 1
            
            return success_response({
                "items": res["result"] or [],
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "has_prev": page > 1,
                    "has_next": page < total_pages
                }
            }, message="Activity logs retrieved successfully")
        except Exception as e:
            return error_response(f"Error fetching activity logs: {str(e)}", status_code=500)
