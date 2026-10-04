from flask import Blueprint
from backend.controllers.form_controller import FormController
from backend.middleware.auth_middleware import require_auth, optional_auth

form_bp = Blueprint("forms", __name__, url_prefix="/api/forms")

# Forms CRUD
form_bp.route("", methods=["GET"])(optional_auth()(FormController.get_all))
form_bp.route("/<int:form_id>", methods=["GET"])(optional_auth()(FormController.get_by_id))
form_bp.route("", methods=["POST"])(require_auth(admin_only=True)(FormController.create))
form_bp.route("/<int:form_id>", methods=["PUT"])(require_auth(admin_only=True)(FormController.update))
form_bp.route("/<int:form_id>", methods=["DELETE"])(require_auth(admin_only=True)(FormController.delete))

# Form Submissions
form_bp.route("/<int:form_id>/submit", methods=["POST"])(optional_auth()(FormController.submit_form))

@form_bp.route("/<int:form_id>/submissions", methods=["GET"])
@require_auth(admin_only=True)
def get_form_submissions(form_id):
    return FormController.get_submissions(form_id)

@form_bp.route("/submissions", methods=["GET"])
@require_auth(admin_only=True)
def get_all_submissions():
    return FormController.get_submissions(None)

form_bp.route("/submissions/<int:sub_id>", methods=["DELETE"])(require_auth(admin_only=True)(FormController.delete_submission))
