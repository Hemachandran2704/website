from flask import Blueprint
from backend.controllers.tabs_controller import TabsController
from backend.middleware.auth_middleware import require_auth, optional_auth

tabs_bp = Blueprint("tabs", __name__, url_prefix="/api/tabs")

tabs_bp.route("", methods=["GET"])(optional_auth()(TabsController.get_all))
tabs_bp.route("/<int:tab_id>", methods=["GET"])(optional_auth()(TabsController.get_by_id))
tabs_bp.route("", methods=["POST"])(require_auth()(TabsController.create))
tabs_bp.route("/<int:tab_id>", methods=["PUT"])(require_auth()(TabsController.update))
tabs_bp.route("/<int:tab_id>", methods=["DELETE"])(require_auth()(TabsController.delete))
