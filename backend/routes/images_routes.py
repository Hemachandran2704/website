from flask import Blueprint
from backend.controllers.images_controller import ImagesController
from backend.middleware.auth_middleware import require_auth, optional_auth

images_bp = Blueprint("images", __name__, url_prefix="/api/images")

images_bp.route("", methods=["GET"])(optional_auth()(ImagesController.get_all))
images_bp.route("/<int:image_id>", methods=["GET"])(optional_auth()(ImagesController.get_by_id))
images_bp.route("", methods=["POST"])(require_auth()(ImagesController.create))
images_bp.route("/<int:image_id>", methods=["PUT"])(require_auth()(ImagesController.update))
images_bp.route("/<int:image_id>", methods=["DELETE"])(require_auth()(ImagesController.delete))
