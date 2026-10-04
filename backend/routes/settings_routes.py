from flask import Blueprint
from backend.controllers.settings_controller import SettingsController
from backend.middleware.auth_middleware import require_auth

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

settings_bp.route("/user", methods=["GET"])(require_auth()(SettingsController.get_user_settings))
settings_bp.route("/user", methods=["PUT"])(require_auth()(SettingsController.update_user_settings))
settings_bp.route("/system", methods=["GET"])(require_auth(admin_only=True)(SettingsController.get_system_settings))
settings_bp.route("/system", methods=["PUT"])(require_auth(admin_only=True)(SettingsController.update_system_settings))
