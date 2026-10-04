import os
import sys
import datetime

# Ensure root directory is in sys.path before importing the backend package.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, send_from_directory, jsonify, redirect, request, session, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from backend.config.database import execute_query
from backend.middleware.auth_middleware import get_token_from_request
from backend.services.auth_service import AuthService

load_dotenv(os.path.join(BASE_DIR, ".env"))

from backend.controllers.auth_controller import AuthController
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.ticket_routes import ticket_bp
from backend.routes.document_routes import document_bp
from backend.routes.settings_routes import settings_bp
from backend.routes.announcement_routes import announcement_bp
from backend.routes.schedule_routes import schedule_bp
from backend.routes.favorite_routes import favorite_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.tabs_routes import tabs_bp
from backend.routes.menu_routes import menu_bp
from backend.routes.autocomplete_routes import autocomplete_bp
from backend.routes.collapsible_routes import collapsible_bp
from backend.routes.images_routes import images_bp
from backend.routes.slider_routes import slider_bp
from backend.routes.tooltip_routes import tooltip_bp
from backend.routes.popup_routes import popup_bp
from backend.routes.links_routes import links_bp
from backend.routes.css_routes import css_bp
from backend.routes.iframe_routes import iframe_bp
from backend.routes.content_routes import content_bp
from backend.routes.media_routes import media_bp
from backend.routes.form_routes import form_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.activity_routes import activity_bp
from backend.routes.reports_routes import reports_bp

app = Flask(__name__, static_folder=None)

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Configuration & Flask Session
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-magnus-cms-key-change-in-production-2026")
app.config["SESSION_COOKIE_NAME"] = "magnus_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
FRONTEND_FOLDER = os.path.join(BASE_DIR, "frontend")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register API blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(ticket_bp)
app.register_blueprint(document_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(announcement_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(favorite_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(tabs_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(autocomplete_bp)
app.register_blueprint(collapsible_bp)
app.register_blueprint(images_bp)
app.register_blueprint(slider_bp)
app.register_blueprint(tooltip_bp)
app.register_blueprint(popup_bp)
app.register_blueprint(links_bp)
app.register_blueprint(css_bp)
app.register_blueprint(iframe_bp)
app.register_blueprint(content_bp)
app.register_blueprint(media_bp)
app.register_blueprint(form_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(reports_bp)


def is_authenticated():
    return bool(session.get("user_id"))


@app.after_request
def add_security_headers(response):
    # Prevent sensitive page caching so browser back button does not display stale auth data
    if request.path in ("/dashboard", "/home", "/admin", "/admin/dashboard", "/login", "/register") or request.path.startswith("/frontend/pages/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# 1. Root URL - Redirect unauthenticated users to /login, authenticated users to dashboard
@app.route("/")
def index():
    return redirect("/login")


# 2. Login Route
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        return AuthController.login()

    return send_from_directory(FRONTEND_FOLDER, "login.html")

# 2b. Register Route
@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        return AuthController.register()
        
    if is_authenticated():
        return redirect("/dashboard")
    return send_from_directory(FRONTEND_FOLDER, "register.html")


# 3. Logout Route
@app.route("/logout", methods=["GET", "POST"])
def logout_route():
    AuthController.logout()
    if request.is_json:
        return jsonify({"success": True, "message": "Logged out successfully"})
    return redirect("/login")


# 4. Protected Dashboard Routes
@app.route("/dashboard")
def dashboard_page():
    if not is_authenticated():
        return redirect("/login")
    return send_from_directory(FRONTEND_FOLDER, "user-dashboard.html")


@app.route("/home")
def home_page():
    if not is_authenticated():
        return redirect("/login")
    return send_from_directory(FRONTEND_FOLDER, "user-dashboard.html")


@app.route("/portal")
def public_portal_page():
    if not is_authenticated():
        return redirect("/login")
    return send_from_directory(FRONTEND_FOLDER, "index.html")


# 4b. Protected Admin Routes
@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard_page():
    if not is_authenticated():
        return redirect("/login")
    return redirect("/dashboard")


# 5. Protected More Route
@app.route("/more")
def more_page():
    if not is_authenticated():
        return redirect("/login")
    return redirect("/frontend/pages/multiple-tabs.html")


# 6. Static file serving: Uploads
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    image = execute_query(
        "SELECT user_id FROM images WHERE file_path = %s LIMIT 1",
        (filename,),
        fetch_one=True,
    )["result"]
    owner_id = image.get("user_id") if image else None
    if owner_id is not None:
        user = None
        token = get_token_from_request()
        if token:
            payload = AuthService.decode_token(token)
            if payload:
                user = AuthService.get_user_by_id(payload.get("id"))
        if not user and session.get("user_id"):
            user = AuthService.get_user_by_id(session.get("user_id"))
        if not user or user.get("status") != "active" or user["id"] != owner_id:
            return jsonify({"success": False, "message": "File not found"}), 404
    return send_from_directory(UPLOAD_FOLDER, filename)


# 7. Static and Protected frontend file serving
@app.route("/frontend/<path:filename>")
def serve_frontend(filename):
    # Allow CSS and JS assets without login so login/register page renders correctly
    if filename.startswith("css/") or filename.startswith("js/"):
        return send_from_directory(FRONTEND_FOLDER, filename)

    # Login and Register pages
    if filename == "login.html":
        if is_authenticated():
            return redirect("/dashboard")
        return send_from_directory(FRONTEND_FOLDER, filename)

    if filename == "register.html":
        if is_authenticated():
            return redirect("/dashboard")
        return send_from_directory(FRONTEND_FOLDER, filename)

    # Protected HTML files
    if filename == "dashboard.html":
        if not is_authenticated():
            return redirect("/login")
        return redirect("/dashboard")

    if filename == "user-dashboard.html":
        if not is_authenticated():
            return redirect("/login")
        return send_from_directory(FRONTEND_FOLDER, "user-dashboard.html")

    # All other HTML files and subpages are protected
    if filename.endswith(".html") or "/pages/" in filename or filename.startswith("pages/"):
        if not is_authenticated():
            return redirect("/login")
        return send_from_directory(FRONTEND_FOLDER, filename)

    # Fallback for images/assets
    return send_from_directory(FRONTEND_FOLDER, filename)


# 8. Shortcut route for /pages/<filename>
@app.route("/pages/<path:filename>")
def serve_pages_shortcut(filename):
    if not is_authenticated():
        return redirect("/login")
    return send_from_directory(os.path.join(FRONTEND_FOLDER, "pages"), filename)


# Standard Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Resource not found", "errors": {"path": "Not found"}}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "message": "HTTP Method not allowed", "errors": {"method": "Not allowed"}}), 405


@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"success": False, "message": "File size exceeds 5MB limit", "errors": {"file": "Too large"}}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error occurred", "errors": {"server": str(e)}}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"Magnus Dynamic CMS running on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug)
