from flask import request, g
from backend.config.database import execute_query, log_audit
from backend.utils.responses import success_response, error_response
from backend.utils.validators import sanitize_input


class TicketController:
    @staticmethod
    def get_tickets():
        """
        Admin gets all tickets with filters (search, status, priority, category).
        Regular user gets ONLY their own tickets.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            is_admin = curr_user.get("role") == "admin"
            status_filter = (request.args.get("status") or "").strip().lower()
            priority_filter = (request.args.get("priority") or "").strip().lower()
            search = (request.args.get("search") or "").strip().lower()

            where_clauses = []
            params = []

            if not is_admin:
                where_clauses.append("t.user_id = %s")
                params.append(curr_user["id"])

            if status_filter in ("open", "in_progress", "resolved", "closed"):
                where_clauses.append("t.status = %s")
                params.append(status_filter)

            if priority_filter in ("low", "medium", "high", "urgent"):
                where_clauses.append("t.priority = %s")
                params.append(priority_filter)

            if search:
                where_clauses.append("(LOWER(t.subject) LIKE %s OR LOWER(t.message) LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
                SELECT t.id, t.user_id, u.name as user_name, u.email as user_email,
                       t.subject, t.message, t.category, t.priority, t.status,
                       t.created_at, t.updated_at,
                       (SELECT COUNT(*) FROM ticket_replies r WHERE r.ticket_id = t.id) as reply_count
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                {where_str}
                ORDER BY t.id DESC
            """
            res = execute_query(query, params, fetch_all=True)
            return success_response(res["result"] or [], message="Support tickets retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch tickets: {str(e)}", status_code=500)

    @staticmethod
    def get_ticket_by_id(ticket_id):
        """
        Gets ticket details along with thread replies.
        Ensures normal user cannot view another user's ticket.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            t_res = execute_query("""
                SELECT t.id, t.user_id, u.name as user_name, u.email as user_email,
                       t.subject, t.message, t.category, t.priority, t.status,
                       t.created_at, t.updated_at
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                WHERE t.id = %s
                LIMIT 1
            """, (ticket_id,), fetch_one=True)

            ticket = t_res["result"]
            if not ticket:
                return error_response("Ticket not found", status_code=404)

            # Security check: User must be admin or ticket creator
            if curr_user.get("role") != "admin" and ticket["user_id"] != curr_user["id"]:
                return error_response("Forbidden: You cannot view another user's ticket", status_code=403)

            # Fetch replies
            r_res = execute_query("""
                SELECT r.id, r.ticket_id, r.user_id, u.name as user_name, u.email as user_email,
                       r.message, r.is_admin, r.created_at
                FROM ticket_replies r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.ticket_id = %s
                ORDER BY r.created_at ASC, r.id ASC
            """, (ticket_id,), fetch_all=True)

            ticket["replies"] = r_res["result"] or []
            return success_response(ticket, message="Ticket details retrieved")
        except Exception as e:
            return error_response(f"Failed to fetch ticket: {str(e)}", status_code=500)

    @staticmethod
    def create_ticket():
        """
        Creates a new support ticket for authenticated user.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            subject = sanitize_input(data.get("subject") or "")
            message = sanitize_input(data.get("message") or "")
            category = sanitize_input(data.get("category") or "General")
            priority = (data.get("priority") or "medium").strip().lower()

            if not subject or len(subject) < 3:
                return error_response("Subject is required (min 3 characters)", status_code=400)
            if not message or len(message) < 5:
                return error_response("Message content is required (min 5 characters)", status_code=400)
            if priority not in ("low", "medium", "high", "urgent"):
                priority = "medium"

            insert_query = """
                INSERT INTO support_tickets (user_id, subject, message, category, priority, status)
                VALUES (%s, %s, %s, %s, %s, 'open')
            """
            res = execute_query(insert_query, (curr_user["id"], subject, message, category, priority), commit=True)
            ticket_id = res["last_id"]

            log_audit(curr_user["id"], "CREATE_TICKET", "TICKETS", ticket_id, f"User created ticket #{ticket_id}: {subject}")
            return success_response({"id": ticket_id, "subject": subject, "status": "open"}, message="Ticket created successfully", status_code=201)
        except Exception as e:
            return error_response(f"Failed to create ticket: {str(e)}", status_code=500)

    @staticmethod
    def add_reply(ticket_id):
        """
        Adds a reply to an existing ticket.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            message = sanitize_input(data.get("message") or "")
            if not message:
                return error_response("Reply message cannot be empty", status_code=400)

            # Check ticket ownership or admin
            t_res = execute_query("SELECT id, user_id, status FROM support_tickets WHERE id = %s", (ticket_id,), fetch_one=True)
            ticket = t_res["result"]
            if not ticket:
                return error_response("Ticket not found", status_code=404)

            is_admin = curr_user.get("role") == "admin"
            if not is_admin and ticket["user_id"] != curr_user["id"]:
                return error_response("Forbidden: You cannot reply to this ticket", status_code=403)

            execute_query("""
                INSERT INTO ticket_replies (ticket_id, user_id, message, is_admin)
                VALUES (%s, %s, %s, %s)
            """, (ticket_id, curr_user["id"], message, 1 if is_admin else 0), commit=True)

            # Update ticket status if admin replied and status was open
            if is_admin and ticket["status"] == "open":
                execute_query("UPDATE support_tickets SET status = 'in_progress' WHERE id = %s", (ticket_id,), commit=True)

            log_audit(curr_user["id"], "REPLY_TICKET", "TICKETS", ticket_id, f"Added reply to ticket #{ticket_id}")
            return success_response(message="Reply added successfully")
        except Exception as e:
            return error_response(f"Failed to add reply: {str(e)}", status_code=500)

    @staticmethod
    def update_status(ticket_id):
        """
        Admin updates status (open, in_progress, resolved, closed).
        Owner can resolve or close their own ticket.
        """
        try:
            curr_user = getattr(g, "current_user", None)
            if not curr_user:
                return error_response("Unauthorized", status_code=401)

            data = request.get_json(silent=True) or {}
            new_status = (data.get("status") or "").strip().lower()
            if new_status not in ("open", "in_progress", "resolved", "closed"):
                return error_response("Invalid status value", status_code=400)

            t_res = execute_query("SELECT id, user_id, status FROM support_tickets WHERE id = %s", (ticket_id,), fetch_one=True)
            ticket = t_res["result"]
            if not ticket:
                return error_response("Ticket not found", status_code=404)

            is_admin = curr_user.get("role") == "admin"
            if not is_admin and ticket["user_id"] != curr_user["id"]:
                return error_response("Forbidden: Access denied", status_code=403)

            execute_query("UPDATE support_tickets SET status = %s WHERE id = %s", (new_status, ticket_id), commit=True)
            log_audit(curr_user["id"], "STATUS_TICKET", "TICKETS", ticket_id, f"Ticket #{ticket_id} status updated to {new_status}")
            return success_response(message=f"Ticket status updated to {new_status}")
        except Exception as e:
            return error_response(f"Failed to update ticket status: {str(e)}", status_code=500)
