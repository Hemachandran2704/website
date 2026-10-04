from flask import Blueprint
from backend.controllers.slider_controller import SliderController
from backend.middleware.auth_middleware import require_auth, optional_auth

slider_bp = Blueprint("slider", __name__, url_prefix="/api/sliders")

slider_bp.route("", methods=["GET"])(optional_auth()(SliderController.get_all))
slider_bp.route("/<int:slider_id>", methods=["GET"])(optional_auth()(SliderController.get_by_id))
slider_bp.route("", methods=["POST"])(require_auth()(SliderController.create))
slider_bp.route("/<int:slider_id>", methods=["PUT"])(require_auth()(SliderController.update))
slider_bp.route("/<int:slider_id>", methods=["DELETE"])(require_auth()(SliderController.delete))
