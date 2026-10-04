from flask import Blueprint
from backend.controllers.document_controller import DocumentController
from backend.middleware.auth_middleware import require_auth

document_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

document_bp.route("", methods=["GET"])(require_auth()(DocumentController.get_documents))
document_bp.route("", methods=["POST"])(require_auth()(DocumentController.upload_document))
document_bp.route("/<int:doc_id>/status", methods=["PUT"])(require_auth(admin_only=True)(DocumentController.update_status))
document_bp.route("/<int:doc_id>", methods=["DELETE"])(require_auth()(DocumentController.delete_document))
