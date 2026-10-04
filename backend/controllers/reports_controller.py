import datetime
from flask import request, g
from backend.config.database import execute_query
from backend.utils.responses import success_response, error_response


class ReportsController:
    @staticmethod
    def get_summary():
        """
        Admin system-wide reports with time filtering (today, 7days, 30days, custom).
        """
        try:
            date_range = (request.args.get("range") or "all").strip().lower()
            start_date = request.args.get("start_date", "").strip()
            end_date = request.args.get("end_date", "").strip()

            date_clause = ""
            date_params = []
            now = datetime.datetime.now()

            if date_range == "today":
                today_str = now.strftime("%Y-%m-%d")
                date_clause = "WHERE created_at >= %s"
                date_params = [f"{today_str} 00:00:00"]
            elif date_range == "7days":
                seven_days_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                date_clause = "WHERE created_at >= %s"
                date_params = [seven_days_ago]
            elif date_range == "30days":
                thirty_days_ago = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                date_clause = "WHERE created_at >= %s"
                date_params = [thirty_days_ago]
            elif date_range == "custom" and start_date:
                if end_date:
                    date_clause = "WHERE created_at >= %s AND created_at <= %s"
                    date_params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
                else:
                    date_clause = "WHERE created_at >= %s"
                    date_params = [f"{start_date} 00:00:00"]

            # General totals
            q_users = execute_query("SELECT COUNT(*) as c FROM users", fetch_one=True)
            q_new_users = execute_query(f"SELECT COUNT(*) as c FROM users {date_clause}", date_params, fetch_one=True)
            q_active_users = execute_query("SELECT COUNT(*) as c FROM users WHERE status = 'active'", fetch_one=True)
            q_inactive_users = execute_query("SELECT COUNT(*) as c FROM users WHERE status != 'active'", fetch_one=True)
            
            q_tabs = execute_query("SELECT COUNT(*) as c FROM tabs", fetch_one=True)
            q_menus = execute_query("SELECT COUNT(*) as c FROM menus", fetch_one=True)
            q_autocomplete = execute_query("SELECT COUNT(*) as c FROM autocomplete_items", fetch_one=True)
            q_collapsible = execute_query("SELECT COUNT(*) as c FROM collapsible_contents", fetch_one=True)
            q_images = execute_query("SELECT COUNT(*) as c FROM images", fetch_one=True)
            q_sliders = execute_query("SELECT COUNT(*) as c FROM sliders", fetch_one=True)
            q_tooltips = execute_query("SELECT COUNT(*) as c FROM tooltips", fetch_one=True)
            q_popups = execute_query("SELECT COUNT(*) as c FROM popups", fetch_one=True)
            q_links = execute_query("SELECT COUNT(*) as c FROM links", fetch_one=True)
            q_css = execute_query("SELECT COUNT(*) as c FROM css_properties", fetch_one=True)
            q_iframes = execute_query("SELECT COUNT(*) as c FROM iframes", fetch_one=True)
            
            q_content = execute_query(f"SELECT COUNT(*) as c FROM content_manager {date_clause}", date_params, fetch_one=True)
            q_media = execute_query(f"SELECT COUNT(*) as c FROM media_manager {date_clause}", date_params, fetch_one=True)
            q_forms = execute_query(f"SELECT COUNT(*) as c FROM forms {date_clause}", date_params, fetch_one=True)
            q_submissions = execute_query(f"SELECT COUNT(*) as c FROM form_submissions {date_clause}", date_params, fetch_one=True)
            q_notifications = execute_query(f"SELECT COUNT(*) as c FROM notifications {date_clause}", date_params, fetch_one=True)
            q_activity = execute_query(f"SELECT COUNT(*) as c FROM activity_logs {date_clause}", date_params, fetch_one=True)
            
            q_tickets = execute_query(f"SELECT COUNT(*) as c FROM support_tickets {date_clause}", date_params, fetch_one=True)
            q_open_tickets = execute_query("SELECT COUNT(*) as c FROM support_tickets WHERE status IN ('open', 'in_progress')", fetch_one=True)
            q_docs = execute_query(f"SELECT COUNT(*) as c FROM documents {date_clause}", date_params, fetch_one=True)
            q_pending_docs = execute_query("SELECT COUNT(*) as c FROM documents WHERE status = 'pending'", fetch_one=True)

            # Breakdowns
            q_role_breakdown = execute_query("SELECT role, COUNT(*) as count FROM users GROUP BY role", fetch_all=True)
            q_content_status = execute_query(f"SELECT status, COUNT(*) as count FROM content_manager {date_clause} GROUP BY status", date_params, fetch_all=True)
            q_notif_type = execute_query(f"SELECT type, COUNT(*) as count FROM notifications {date_clause} GROUP BY type", date_params, fetch_all=True)
            q_action_breakdown = execute_query(f"SELECT action, COUNT(*) as count FROM activity_logs {date_clause} GROUP BY action", date_params, fetch_all=True)
            q_ticket_status = execute_query("SELECT status, COUNT(*) as count FROM support_tickets GROUP BY status", fetch_all=True)
            
            # Recent activity logs
            date_clause_al = date_clause.replace("created_at", "al.created_at") if date_clause else ""
            recent_q = f"""
                SELECT al.id, al.action, al.module, al.description, al.created_at,
                       COALESCE(u.name, 'System') as user_name
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.id
                {date_clause_al}
                ORDER BY al.id DESC
                LIMIT 10
            """
            recent_res = execute_query(recent_q, date_params, fetch_all=True)
            
            stats = {
                "total_users": q_users["result"]["c"] if q_users["result"] else 0,
                "new_users": q_new_users["result"]["c"] if q_new_users["result"] else 0,
                "active_users": q_active_users["result"]["c"] if q_active_users["result"] else 0,
                "inactive_users": q_inactive_users["result"]["c"] if q_inactive_users["result"] else 0,
                "total_tabs": q_tabs["result"]["c"] if q_tabs["result"] else 0,
                "total_menus": q_menus["result"]["c"] if q_menus["result"] else 0,
                "total_autocomplete": q_autocomplete["result"]["c"] if q_autocomplete["result"] else 0,
                "total_collapsible": q_collapsible["result"]["c"] if q_collapsible["result"] else 0,
                "total_images": q_images["result"]["c"] if q_images["result"] else 0,
                "total_sliders": q_sliders["result"]["c"] if q_sliders["result"] else 0,
                "total_tooltips": q_tooltips["result"]["c"] if q_tooltips["result"] else 0,
                "total_popups": q_popups["result"]["c"] if q_popups["result"] else 0,
                "total_links": q_links["result"]["c"] if q_links["result"] else 0,
                "total_css": q_css["result"]["c"] if q_css["result"] else 0,
                "total_iframes": q_iframes["result"]["c"] if q_iframes["result"] else 0,
                "total_content": q_content["result"]["c"] if q_content["result"] else 0,
                "total_media": q_media["result"]["c"] if q_media["result"] else 0,
                "total_forms": q_forms["result"]["c"] if q_forms["result"] else 0,
                "total_form_submissions": q_submissions["result"]["c"] if q_submissions["result"] else 0,
                "total_submissions": q_submissions["result"]["c"] if q_submissions["result"] else 0,
                "total_notifications": q_notifications["result"]["c"] if q_notifications["result"] else 0,
                "total_activity_logs": q_activity["result"]["c"] if q_activity["result"] else 0,
                "total_tickets": q_tickets["result"]["c"] if q_tickets["result"] else 0,
                "open_tickets": q_open_tickets["result"]["c"] if q_open_tickets["result"] else 0,
                "total_documents": q_docs["result"]["c"] if q_docs["result"] else 0,
                "pending_documents": q_pending_docs["result"]["c"] if q_pending_docs["result"] else 0,
                "role_breakdown": q_role_breakdown["result"] or [],
                "content_status_breakdown": q_content_status["result"] or [],
                "notification_type_breakdown": q_notif_type["result"] or [],
                "action_breakdown": q_action_breakdown["result"] or [],
                "ticket_status_breakdown": q_ticket_status["result"] or [],
                "recent_activities": recent_res["result"] or [],
                "filter_range": date_range
            }
            
            return success_response(stats, message="Reports summary calculated successfully")
        except Exception as e:
            return error_response(f"Error generating reports: {str(e)}", status_code=500)

    @staticmethod
    def get_user_report():
        """
        Personal report metrics for authenticated regular user.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            uid = curr_user["id"]
            q_tickets = execute_query("SELECT COUNT(*) as c FROM support_tickets WHERE user_id = %s", (uid,), fetch_one=True)
            q_resolved_tickets = execute_query("SELECT COUNT(*) as c FROM support_tickets WHERE user_id = %s AND status = 'resolved'", (uid,), fetch_one=True)
            q_docs = execute_query("SELECT COUNT(*) as c FROM documents WHERE user_id = %s", (uid,), fetch_one=True)
            q_approved_docs = execute_query("SELECT COUNT(*) as c FROM documents WHERE user_id = %s AND status = 'approved'", (uid,), fetch_one=True)
            q_activities = execute_query("SELECT COUNT(*) as c FROM activity_logs WHERE user_id = %s", (uid,), fetch_one=True)

            action_breakdown = execute_query("SELECT action, COUNT(*) as count FROM activity_logs WHERE user_id = %s GROUP BY action", (uid,), fetch_all=True)

            report = {
                "total_tickets": q_tickets["result"]["c"] if q_tickets["result"] else 0,
                "resolved_tickets": q_resolved_tickets["result"]["c"] if q_resolved_tickets["result"] else 0,
                "total_documents": q_docs["result"]["c"] if q_docs["result"] else 0,
                "approved_documents": q_approved_docs["result"]["c"] if q_approved_docs["result"] else 0,
                "total_activities": q_activities["result"]["c"] if q_activities["result"] else 0,
                "action_breakdown": action_breakdown["result"] or [],
                "user_name": curr_user.get("name", "User"),
                "user_email": curr_user.get("email", ""),
                "member_since": str(curr_user.get("created_at", ""))
            }
            return success_response(report, message="User personal report retrieved")
        except Exception as e:
            return error_response(f"Error generating user report: {str(e)}", status_code=500)
