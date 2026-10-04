import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MEDIA_ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "pdf", "doc", "docx", "xls", "xlsx",
    "ppt", "pptx", "txt", "csv", "mp4", "webm", "mov"
}
MAX_FILE_SIZE = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB


class UploadService:
    @staticmethod
    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @classmethod
    def save_image(cls, file_obj):
        """
        Validates and safely stores an uploaded image file.
        Returns (relative_file_path, None) or (None, error_message).
        """
        if not file_obj or file_obj.filename == "":
            return None, "No file selected."
            
        if not cls.allowed_file(file_obj.filename):
            return None, f"Unsupported file type. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

        # Read file size / seek
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)
        
        if size > MAX_FILE_SIZE:
            return None, f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate safe unique filename
        ext = file_obj.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        target_path = os.path.join(UPLOAD_FOLDER, unique_name)
        
        file_obj.save(target_path)
        return unique_name, None

    @classmethod
    def save_media(cls, file_obj):
        """Safely stores supported image, document, or video media."""
        if not file_obj or file_obj.filename == "":
            return None, "No file selected."

        if "." not in file_obj.filename or file_obj.filename.rsplit(".", 1)[1].lower() not in MEDIA_ALLOWED_EXTENSIONS:
            return None, f"Unsupported file type. Allowed formats: {', '.join(sorted(MEDIA_ALLOWED_EXTENSIONS))}."

        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)

        if size > MAX_FILE_SIZE:
            return None, f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        ext = file_obj.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        target_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file_obj.save(target_path)
        return unique_name, None

    @classmethod
    def delete_image_file(cls, filename):
        if not filename:
            return
        # Prevent directory traversal
        safe_name = os.path.basename(filename)
        path = os.path.join(UPLOAD_FOLDER, safe_name)
        if os.path.exists(path) and os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file {path}: {e}")
