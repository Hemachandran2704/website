from flask import Blueprint
from backend.controllers.autocomplete_controller import AutocompleteController
from backend.middleware.auth_middleware import require_auth, optional_auth

autocomplete_bp = Blueprint("autocomplete", __name__, url_prefix="/api/autocomplete")

autocomplete_bp.route("", methods=["GET"])(optional_auth()(AutocompleteController.get_all))
autocomplete_bp.route("/search", methods=["GET"])(optional_auth()(AutocompleteController.search))
autocomplete_bp.route("/<int:item_id>", methods=["GET"])(optional_auth()(AutocompleteController.get_by_id))
autocomplete_bp.route("", methods=["POST"])(require_auth()(AutocompleteController.create))
autocomplete_bp.route("/<int:item_id>", methods=["PUT"])(require_auth()(AutocompleteController.update))
autocomplete_bp.route("/<int:item_id>", methods=["DELETE"])(require_auth()(AutocompleteController.delete))
