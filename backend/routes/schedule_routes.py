from flask import Blueprint
from backend.controllers.schedule_controller import ScheduleController
from backend.middleware.auth_middleware import require_auth

schedule_bp = Blueprint("schedules", __name__, url_prefix="/api/user/schedules")

schedule_bp.route("", methods=["GET"])(require_auth()(ScheduleController.get_schedules))
schedule_bp.route("", methods=["POST"])(require_auth()(ScheduleController.create_schedule))
schedule_bp.route("/<int:schedule_id>", methods=["DELETE"])(require_auth()(ScheduleController.delete_schedule))
