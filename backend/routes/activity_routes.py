from flask import Blueprint
from backend.controllers.activity_controller import ActivityController
from backend.middleware.auth_middleware import require_auth

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity-logs")

activity_bp.route("", methods=["GET"])(require_auth(admin_only=True)(ActivityController.get_all))
