from flask import Blueprint
from backend.controllers.content_controller import ContentController
from backend.middleware.auth_middleware import require_auth, optional_auth

content_bp = Blueprint("content", __name__, url_prefix="/api/content")

content_bp.route("", methods=["GET"])(optional_auth()(ContentController.get_all))
content_bp.route("/<int:content_id>", methods=["GET"])(optional_auth()(ContentController.get_by_id))
content_bp.route("", methods=["POST"])(require_auth(admin_only=True)(ContentController.create))
content_bp.route("/<int:content_id>", methods=["PUT"])(require_auth(admin_only=True)(ContentController.update))
content_bp.route("/<int:content_id>", methods=["DELETE"])(require_auth(admin_only=True)(ContentController.delete))
