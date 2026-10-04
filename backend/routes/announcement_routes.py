from flask import Blueprint
from backend.controllers.announcement_controller import AnnouncementController
from backend.middleware.auth_middleware import require_auth

announcement_bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")

announcement_bp.route("", methods=["GET"])(require_auth()(AnnouncementController.get_announcements))
announcement_bp.route("", methods=["POST"])(require_auth(admin_only=True)(AnnouncementController.create_announcement))
announcement_bp.route("/<int:ann_id>", methods=["PUT"])(require_auth(admin_only=True)(AnnouncementController.update_announcement))
announcement_bp.route("/<int:ann_id>", methods=["DELETE"])(require_auth(admin_only=True)(AnnouncementController.delete_announcement))
