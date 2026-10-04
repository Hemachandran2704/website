from flask import Blueprint
from backend.controllers.collapsible_controller import CollapsibleController
from backend.middleware.auth_middleware import require_auth, optional_auth

collapsible_bp = Blueprint("collapsible", __name__, url_prefix="/api/collapsible")

collapsible_bp.route("", methods=["GET"])(optional_auth()(CollapsibleController.get_all))
collapsible_bp.route("/<int:item_id>", methods=["GET"])(optional_auth()(CollapsibleController.get_by_id))
collapsible_bp.route("", methods=["POST"])(require_auth()(CollapsibleController.create))
collapsible_bp.route("/<int:item_id>", methods=["PUT"])(require_auth()(CollapsibleController.update))
collapsible_bp.route("/<int:item_id>", methods=["DELETE"])(require_auth()(CollapsibleController.delete))
