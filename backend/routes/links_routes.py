from flask import Blueprint
from backend.controllers.links_controller import LinksController
from backend.middleware.auth_middleware import require_auth, optional_auth

links_bp = Blueprint("links", __name__, url_prefix="/api/links")

links_bp.route("", methods=["GET"])(optional_auth()(LinksController.get_all))
links_bp.route("/<int:link_id>", methods=["GET"])(optional_auth()(LinksController.get_by_id))
links_bp.route("", methods=["POST"])(require_auth()(LinksController.create))
links_bp.route("/<int:link_id>", methods=["PUT"])(require_auth()(LinksController.update))
links_bp.route("/<int:link_id>", methods=["DELETE"])(require_auth()(LinksController.delete))
