from flask import Blueprint
from backend.controllers.user_controller import UserController
from backend.middleware.auth_middleware import require_auth

user_bp = Blueprint("users", __name__, url_prefix="/api")

# Admin-only user management
user_bp.route("/users", methods=["GET"])(require_auth(admin_only=True)(UserController.get_users))
user_bp.route("/users", methods=["POST"])(require_auth(admin_only=True)(UserController.create_user))
user_bp.route("/users/<int:user_id>", methods=["GET"])(require_auth()(UserController.get_user_by_id))
user_bp.route("/users/<int:user_id>", methods=["PUT"])(require_auth(admin_only=True)(UserController.update_user))
user_bp.route("/users/<int:user_id>/status", methods=["PUT"])(require_auth(admin_only=True)(UserController.update_status))
user_bp.route("/users/<int:user_id>", methods=["DELETE"])(require_auth(admin_only=True)(UserController.delete_user))

# Authenticated user own profile & password
user_bp.route("/user/profile", methods=["GET"])(require_auth()(UserController.get_profile))
user_bp.route("/user/profile", methods=["PUT"])(require_auth()(UserController.update_profile))
user_bp.route("/user/password", methods=["PUT"])(require_auth()(UserController.change_password))
