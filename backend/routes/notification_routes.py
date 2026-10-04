from flask import Blueprint
from backend.controllers.notification_controller import NotificationController
from backend.middleware.auth_middleware import require_auth, optional_auth

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

notification_bp.route("", methods=["GET"])(optional_auth()(NotificationController.get_all))
notification_bp.route("/<int:notif_id>", methods=["GET"])(optional_auth()(NotificationController.get_by_id))
notification_bp.route("", methods=["POST"])(require_auth(admin_only=True)(NotificationController.create))
notification_bp.route("/<int:notif_id>", methods=["PUT"])(require_auth(admin_only=True)(NotificationController.update))
notification_bp.route("/<int:notif_id>/read", methods=["PUT"])(require_auth()(NotificationController.mark_as_read))
notification_bp.route("/<int:notif_id>", methods=["DELETE"])(require_auth(admin_only=True)(NotificationController.delete))
