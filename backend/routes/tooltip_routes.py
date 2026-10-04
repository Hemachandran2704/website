from flask import Blueprint
from backend.controllers.tooltip_controller import TooltipController
from backend.middleware.auth_middleware import require_auth, optional_auth

tooltip_bp = Blueprint("tooltip", __name__, url_prefix="/api/tooltips")

tooltip_bp.route("", methods=["GET"])(optional_auth()(TooltipController.get_all))
tooltip_bp.route("/<int:tooltip_id>", methods=["GET"])(optional_auth()(TooltipController.get_by_id))
tooltip_bp.route("", methods=["POST"])(require_auth()(TooltipController.create))
tooltip_bp.route("/<int:tooltip_id>", methods=["PUT"])(require_auth()(TooltipController.update))
tooltip_bp.route("/<int:tooltip_id>", methods=["DELETE"])(require_auth()(TooltipController.delete))
