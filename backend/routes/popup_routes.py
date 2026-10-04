from flask import Blueprint
from backend.controllers.popup_controller import PopupController
from backend.middleware.auth_middleware import require_auth, optional_auth

popup_bp = Blueprint("popup", __name__, url_prefix="/api/popups")

popup_bp.route("", methods=["GET"])(optional_auth()(PopupController.get_all))
popup_bp.route("/<int:popup_id>", methods=["GET"])(optional_auth()(PopupController.get_by_id))
popup_bp.route("", methods=["POST"])(require_auth()(PopupController.create))
popup_bp.route("/<int:popup_id>", methods=["PUT"])(require_auth()(PopupController.update))
popup_bp.route("/<int:popup_id>", methods=["DELETE"])(require_auth()(PopupController.delete))
