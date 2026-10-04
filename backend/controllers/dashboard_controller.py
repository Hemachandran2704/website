from flask import request, g
from backend.config.database import execute_query
from backend.utils.responses import success_response, error_response


class DashboardController:
    @staticmethod
    def get_stats():
        try:
            stats = {}
            queries = {
                "total_tabs": "SELECT COUNT(*) as cnt FROM tabs",
                "total_menus": "SELECT COUNT(*) as cnt FROM menus",
                "total_images": "SELECT COUNT(*) as cnt FROM images",
                "total_sliders": "SELECT COUNT(*) as cnt FROM sliders",
                "total_tooltips": "SELECT COUNT(*) as cnt FROM tooltips",
                "total_popups": "SELECT COUNT(*) as cnt FROM popups",
                "total_links": "SELECT COUNT(*) as cnt FROM links",
                "total_iframes": "SELECT COUNT(*) as cnt FROM iframes",
                "total_users": "SELECT COUNT(*) as cnt FROM users",
                "active_users": "SELECT COUNT(*) as cnt FROM users WHERE status = 'active'",
                "inactive_users": "SELECT COUNT(*) as cnt FROM users WHERE status = 'inactive'",
                "blocked_users": "SELECT COUNT(*) as cnt FROM users WHERE status = 'blocked'",
                "admin_users": "SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'",
                "regular_users": "SELECT COUNT(*) as cnt FROM users WHERE role = 'user'",
                "total_autocomplete": "SELECT COUNT(*) as cnt FROM autocomplete_items",
                "total_collapsible": "SELECT COUNT(*) as cnt FROM collapsible_contents",
                "total_content": "SELECT COUNT(*) as cnt FROM content_manager",
                "total_media": "SELECT COUNT(*) as cnt FROM media_manager",
                "total_forms": "SELECT COUNT(*) as cnt FROM forms",
                "total_submissions": "SELECT COUNT(*) as cnt FROM form_submissions",
                "total_notifications": "SELECT COUNT(*) as cnt FROM notifications",
                "total_tickets": "SELECT COUNT(*) as cnt FROM support_tickets",
                "open_tickets": "SELECT COUNT(*) as cnt FROM support_tickets WHERE status IN ('open', 'in_progress')",
                "resolved_tickets": "SELECT COUNT(*) as cnt FROM support_tickets WHERE status = 'resolved'",
                "total_documents": "SELECT COUNT(*) as cnt FROM documents",
                "pending_documents": "SELECT COUNT(*) as cnt FROM documents WHERE status = 'pending'",
                "approved_documents": "SELECT COUNT(*) as cnt FROM documents WHERE status = 'approved'",
                "total_announcements": "SELECT COUNT(*) as cnt FROM announcements WHERE status = 'active'"
            }
            
            for key, q in queries.items():
                res = execute_query(q, fetch_one=True)
                stats[key] = res["result"]["cnt"] if res["result"] else 0
                
            return success_response(stats, message="Dashboard statistics retrieved successfully")
        except Exception as e:
            return error_response(f"Failed to fetch statistics: {str(e)}", status_code=500)

    @staticmethod
    def get_user_overview():
        """
        User overview metrics for regular users.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            uid = curr_user["id"]
            queries = {
                "my_tickets": ("SELECT COUNT(*) as cnt FROM support_tickets WHERE user_id = %s", (uid,)),
                "open_tickets": ("SELECT COUNT(*) as cnt FROM support_tickets WHERE user_id = %s AND status IN ('open', 'in_progress')", (uid,)),
                "my_documents": ("SELECT COUNT(*) as cnt FROM documents WHERE user_id = %s", (uid,)),
                "approved_documents": ("SELECT COUNT(*) as cnt FROM documents WHERE user_id = %s AND status = 'approved'", (uid,)),
                "pending_documents": ("SELECT COUNT(*) as cnt FROM documents WHERE user_id = %s AND status = 'pending'", (uid,)),
                "my_notifications": ("SELECT COUNT(*) as cnt FROM notifications WHERE (user_id IS NULL OR user_id = %s) AND status = 'active'", (uid,)),
                "my_schedules": ("SELECT COUNT(*) as cnt FROM user_schedules WHERE user_id = %s", (uid,)),
                "my_favorites": ("SELECT COUNT(*) as cnt FROM user_favorites WHERE user_id = %s", (uid,)),
                "my_activities": ("SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id = %s", (uid,))
            }

            stats = {}
            for key, (q, params) in queries.items():
                res = execute_query(q, params, fetch_one=True)
                stats[key] = res["result"]["cnt"] if res["result"] else 0

            # Get recent 5 activities
            act_res = execute_query("""
                SELECT action, module, description, created_at
                FROM activity_logs
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 5
            """, (uid,), fetch_all=True)
            stats["recent_activities"] = act_res["result"] or []

            # Get active announcements
            ann_res = execute_query("""
                SELECT id, title, message, priority, created_at
                FROM announcements
                WHERE status = 'active' AND (target_role = 'all' OR target_role = 'user')
                ORDER BY id DESC
                LIMIT 3
            """, fetch_all=True)
            stats["announcements"] = ann_res["result"] or []

            return success_response(stats, message="User overview retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch user overview: {str(e)}", status_code=500)

    @staticmethod
    def get_audit_logs():
        try:
            limit = int(request.args.get("limit", 25))
            page = int(request.args.get("page", 1))
            module_filter = request.args.get("module", "").strip()
            
            offset = (page - 1) * limit
            
            where_clauses = []
            params = []
            if module_filter:
                where_clauses.append("a.module = %s")
                params.append(module_filter.upper())
                
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            count_query = f"SELECT COUNT(*) as total FROM audit_logs a {where_str}"
            total_res = execute_query(count_query, params, fetch_one=True)
            total = total_res["result"]["total"] if total_res["result"] else 0
            
            data_query = f"""
                SELECT a.id, a.user_id, u.name as user_name, u.email as user_email,
                       a.action, a.module, a.record_id, a.description,
                       a.created_at
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                {where_str}
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT %s OFFSET %s
            """
            data_params = list(params) + [limit, offset]
            logs_res = execute_query(data_query, data_params, fetch_all=True)
            
            return success_response({
                "items": logs_res["result"] or [],
                "total": total,
                "page": page,
                "limit": limit
            }, message="Audit logs retrieved successfully")
        except Exception as e:
            return error_response(f"Failed to fetch audit logs: {str(e)}", status_code=500)

    @staticmethod
    def get_user_activities():
        """
        User's personal activities log.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            limit = int(request.args.get("limit", 25))
            page = int(request.args.get("page", 1))
            offset = (page - 1) * limit

            count_res = execute_query("SELECT COUNT(*) as total FROM activity_logs WHERE user_id = %s", (curr_user["id"],), fetch_one=True)
            total = count_res["result"]["total"] if count_res["result"] else 0

            logs_res = execute_query("""
                SELECT id, user_id, action, module, record_id, description, created_at
                FROM activity_logs
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
            """, (curr_user["id"], limit, offset), fetch_all=True)

            return success_response({
                "items": logs_res["result"] or [],
                "total": total,
                "page": page,
                "limit": limit
            }, message="Personal activity logs retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch personal activities: {str(e)}", status_code=500)
