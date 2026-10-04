from flask import Blueprint
from backend.controllers.media_controller import MediaController
from backend.middleware.auth_middleware import require_auth, optional_auth

media_bp = Blueprint("media", __name__, url_prefix="/api/media")

media_bp.route("", methods=["GET"])(optional_auth()(MediaController.get_all))
media_bp.route("/<int:media_id>", methods=["GET"])(optional_auth()(MediaController.get_by_id))
media_bp.route("", methods=["POST"])(require_auth(admin_only=True)(MediaController.create))
media_bp.route("/<int:media_id>", methods=["PUT"])(require_auth(admin_only=True)(MediaController.update))
media_bp.route("/<int:media_id>", methods=["DELETE"])(require_auth(admin_only=True)(MediaController.delete))
