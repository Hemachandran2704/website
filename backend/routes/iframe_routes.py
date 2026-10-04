from flask import Blueprint
from backend.controllers.iframe_controller import IframeController
from backend.middleware.auth_middleware import require_auth, optional_auth

iframe_bp = Blueprint("iframes", __name__, url_prefix="/api/iframes")

iframe_bp.route("", methods=["GET"])(optional_auth()(IframeController.get_all))
iframe_bp.route("/<int:iframe_id>", methods=["GET"])(optional_auth()(IframeController.get_by_id))
iframe_bp.route("", methods=["POST"])(require_auth()(IframeController.create))
iframe_bp.route("/<int:iframe_id>", methods=["PUT"])(require_auth()(IframeController.update))
iframe_bp.route("/<int:iframe_id>", methods=["DELETE"])(require_auth()(IframeController.delete))
