from flask import Blueprint
from backend.controllers.css_controller import CssController
from backend.middleware.auth_middleware import require_auth, optional_auth

css_bp = Blueprint("css_properties", __name__, url_prefix="/api/css-properties")

css_bp.route("", methods=["GET"])(optional_auth()(CssController.get_all))
css_bp.route("/<int:prop_id>", methods=["GET"])(optional_auth()(CssController.get_by_id))
css_bp.route("", methods=["POST"])(require_auth()(CssController.create))
css_bp.route("/<int:prop_id>", methods=["PUT"])(require_auth()(CssController.update))
css_bp.route("/<int:prop_id>", methods=["DELETE"])(require_auth()(CssController.delete))
