from flask import Blueprint
from backend.controllers.auth_controller import AuthController
from backend.middleware.auth_middleware import require_auth, optional_auth

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

auth_bp.route("/login", methods=["POST"])(AuthController.login)
auth_bp.route("/register", methods=["POST"])(AuthController.register)
auth_bp.route("/logout", methods=["POST", "GET"])(optional_auth()(AuthController.logout))
auth_bp.route("/me", methods=["GET"])(require_auth()(AuthController.me))
