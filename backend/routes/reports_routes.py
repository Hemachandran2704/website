from flask import Blueprint
from backend.controllers.reports_controller import ReportsController
from backend.middleware.auth_middleware import require_auth

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

reports_bp.route("", methods=["GET"])(require_auth(admin_only=True)(ReportsController.get_summary))
reports_bp.route("/", methods=["GET"], endpoint="get_summary_root")(require_auth(admin_only=True)(ReportsController.get_summary))
reports_bp.route("/summary", methods=["GET"], endpoint="get_summary_alias")(require_auth(admin_only=True)(ReportsController.get_summary))
reports_bp.route("/user", methods=["GET"])(require_auth()(ReportsController.get_user_report))

