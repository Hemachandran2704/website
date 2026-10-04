from flask import Blueprint
from backend.controllers.favorite_controller import FavoriteController
from backend.middleware.auth_middleware import require_auth

favorite_bp = Blueprint("favorites", __name__, url_prefix="/api/user/favorites")

favorite_bp.route("", methods=["GET"])(require_auth()(FavoriteController.get_favorites))
favorite_bp.route("", methods=["POST"])(require_auth()(FavoriteController.add_favorite))
favorite_bp.route("/<int:fav_id>", methods=["DELETE"])(require_auth()(FavoriteController.delete_favorite))
