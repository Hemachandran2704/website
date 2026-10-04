from flask import Blueprint
from backend.controllers.ticket_controller import TicketController
from backend.middleware.auth_middleware import require_auth

ticket_bp = Blueprint("tickets", __name__, url_prefix="/api/tickets")

ticket_bp.route("", methods=["GET"])(require_auth()(TicketController.get_tickets))
ticket_bp.route("", methods=["POST"])(require_auth()(TicketController.create_ticket))
ticket_bp.route("/<int:ticket_id>", methods=["GET"])(require_auth()(TicketController.get_ticket_by_id))
ticket_bp.route("/<int:ticket_id>/reply", methods=["POST"])(require_auth()(TicketController.add_reply))
ticket_bp.route("/<int:ticket_id>/status", methods=["PUT"])(require_auth()(TicketController.update_status))
