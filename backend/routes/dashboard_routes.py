from flask import Blueprint
from backend.controllers.dashboard_controller import DashboardController
from backend.middleware.auth_middleware import require_auth

dashboard_bp = Blueprint("dashboard", __name__)

# Admin stats & audit logs
dashboard_bp.route("/api/dashboard/stats", methods=["GET"])(require_auth(admin_only=True)(DashboardController.get_stats))
dashboard_bp.route("/api/audit-logs", methods=["GET"])(require_auth(admin_only=True)(DashboardController.get_audit_logs))

# User overview & personal activities
dashboard_bp.route("/api/user/overview", methods=["GET"])(require_auth()(DashboardController.get_user_overview))
dashboard_bp.route("/api/dashboard/overview", methods=["GET"], endpoint="get_user_overview_alt")(require_auth()(DashboardController.get_user_overview))
dashboard_bp.route("/api/user/activities", methods=["GET"])(require_auth()(DashboardController.get_user_activities))

