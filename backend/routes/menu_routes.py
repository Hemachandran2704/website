from flask import Blueprint
from backend.controllers.menu_controller import MenuController
from backend.middleware.auth_middleware import require_auth, optional_auth

menu_bp = Blueprint("menu", __name__, url_prefix="/api/menus")

menu_bp.route("", methods=["GET"])(optional_auth()(MenuController.get_all))
menu_bp.route("/<int:menu_id>", methods=["GET"])(optional_auth()(MenuController.get_by_id))
menu_bp.route("", methods=["POST"])(require_auth()(MenuController.create))
menu_bp.route("/<int:menu_id>", methods=["PUT"])(require_auth()(MenuController.update))
menu_bp.route("/<int:menu_id>", methods=["DELETE"])(require_auth()(MenuController.delete))
