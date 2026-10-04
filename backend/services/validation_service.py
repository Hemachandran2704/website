from backend.utils.validators import (
    is_valid_email,
    is_valid_status,
    is_allowed_css_property,
    is_safe_css_value,
    is_safe_url,
    is_valid_integer
)

class ValidationService:
    @staticmethod
    def validate_user_login(data):
        errors = {}
        if not data.get("email"):
            errors["email"] = "Email is required."
        elif not is_valid_email(data.get("email")):
            errors["email"] = "Valid email address is required."
            
        if not data.get("password"):
            errors["password"] = "Password is required."
        return len(errors) == 0, errors

    @staticmethod
    def validate_user_registration(data):
        errors = {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password")

        if not name:
            errors["name"] = "Full name is required."
        elif len(name) > 100:
            errors["name"] = "Name must not exceed 100 characters."

        if not email:
            errors["email"] = "Email address is required."
        elif not is_valid_email(email):
            errors["email"] = "A valid email address is required."

        if not password:
            errors["password"] = "Password is required."
        elif len(password) < 6:
            errors["password"] = "Password must be at least 6 characters long."

        if confirm_password is not None and confirm_password != password:
            errors["confirm_password"] = "Passwords do not match."

        return len(errors) == 0, errors

    @staticmethod
    def validate_tab(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Title is required (up to 200 chars)."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Title must not exceed 200 characters."
            
        if not data.get("content") or not data.get("content").strip():
            errors["content"] = "Content is required."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_menu(data):
        errors = {}
        if not data.get("name") or not data.get("name").strip():
            errors["name"] = "Menu name is required (up to 100 chars)."
        elif len(data.get("name").strip()) > 100:
            errors["name"] = "Menu name must not exceed 100 characters."
            
        if not data.get("url") or not data.get("url").strip():
            errors["url"] = "URL is required."
        elif not is_safe_url(data.get("url")):
            errors["url"] = "Invalid or unsafe URL format."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        if data.get("parent_id") is not None and data.get("parent_id") != "":
            if not is_valid_integer(data.get("parent_id"), min_val=1):
                errors["parent_id"] = "Parent ID must be a positive integer or null."
                
        return len(errors) == 0, errors

    @staticmethod
    def validate_autocomplete(data):
        errors = {}
        if not data.get("label") or not data.get("label").strip():
            errors["label"] = "Label is required."
        elif len(data.get("label").strip()) > 200:
            errors["label"] = "Label must not exceed 200 characters."
            
        if not data.get("value") or not data.get("value").strip():
            errors["value"] = "Value is required."
        elif len(data.get("value").strip()) > 200:
            errors["value"] = "Value must not exceed 200 characters."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_collapsible(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Title must not exceed 200 characters."
            
        if not data.get("content") or not data.get("content").strip():
            errors["content"] = "Content is required."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_image_metadata(data, is_update=False):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Image title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Image title must not exceed 200 characters."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_slider(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Slider title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Slider title must not exceed 200 characters."
            
        if not data.get("image_id") or not is_valid_integer(data.get("image_id"), min_val=1):
            errors["image_id"] = "A valid associated image_id is required."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_tooltip(data):
        errors = {}
        if not data.get("element_name") or not data.get("element_name").strip():
            errors["element_name"] = "Element name/identifier is required."
            
        if not data.get("content") or not data.get("content").strip():
            errors["content"] = "Tooltip content text is required."
            
        if data.get("position") not in ("top", "bottom", "left", "right"):
            errors["position"] = "Position must be one of: top, bottom, left, right."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_popup(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Popup title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Popup title must not exceed 200 characters."
            
        if not data.get("content") or not data.get("content").strip():
            errors["content"] = "Popup content is required."
            
        if data.get("trigger_type") not in ("button_click", "page_load", "manual"):
            errors["trigger_type"] = "Trigger type must be: button_click, page_load, or manual."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_link(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Link title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Link title must not exceed 200 characters."
            
        if not data.get("url") or not data.get("url").strip():
            errors["url"] = "Link URL is required."
        elif not is_safe_url(data.get("url")):
            errors["url"] = "URL is invalid or uses an unsafe protocol."
            
        if data.get("target") not in ("_self", "_blank"):
            errors["target"] = "Target must be '_self' or '_blank'."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_css_property(data):
        errors = {}
        prop = data.get("property_name", "").strip().lower()
        if not prop:
            errors["property_name"] = "Property name is required."
        elif not is_allowed_css_property(prop):
            errors["property_name"] = f"Property '{prop}' is not in the allowed whitelist."
            
        val = data.get("property_value", "").strip()
        if not val:
            errors["property_value"] = "Property value is required."
        elif not is_safe_css_value(val):
            errors["property_value"] = "Property value contains unsafe patterns or is invalid."
            
        selector = data.get("selector", "").strip()
        if not selector:
            errors["selector"] = "CSS selector is required."
        elif len(selector) > 100 or "<" in selector or ">" in selector and "script" in selector.lower():
            errors["selector"] = "Selector is invalid or too long."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_iframe(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "iFrame title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Title must not exceed 200 characters."
            
        url = data.get("url", "").strip()
        if not url:
            errors["url"] = "iFrame URL is required."
        elif not is_safe_url(url) or (not url.startswith("https://") and not url.startswith("/")):
            errors["url"] = "iFrame URL must be a secure HTTPS URL or safe local path."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_content(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Title is required (up to 200 chars)."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Title must not exceed 200 characters."
            
        if not data.get("content") or not data.get("content").strip():
            errors["content"] = "Content is required."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        if "display_order" in data and not is_valid_integer(data.get("display_order")):
            errors["display_order"] = "Display order must be an integer."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_media(data):
        errors = {}
        if not data.get("file_name") or not data.get("file_name").strip():
            errors["file_name"] = "File name is required."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_form(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Form title is required (up to 200 chars)."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Form title must not exceed 200 characters."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_form_field(data):
        errors = {}
        if not data.get("field_label") or not data.get("field_label").strip():
            errors["field_label"] = "Field label is required."
            
        if not data.get("field_name") or not data.get("field_name").strip():
            errors["field_name"] = "Field name (key) is required."
            
        allowed_types = ["text", "email", "phone", "textarea", "dropdown", "checkbox", "radio"]
        field_type = data.get("field_type", "text").lower().strip()
        if field_type not in allowed_types:
            errors["field_type"] = f"Field type must be one of: {', '.join(allowed_types)}."
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_notification(data):
        errors = {}
        if not data.get("title") or not data.get("title").strip():
            errors["title"] = "Notification title is required."
        elif len(data.get("title").strip()) > 200:
            errors["title"] = "Notification title must not exceed 200 characters."
            
        if not data.get("message") or not data.get("message").strip():
            errors["message"] = "Notification message is required."
            
        allowed_types = ["info", "success", "warning", "alert"]
        notif_type = data.get("type", "info").lower().strip()
        if notif_type not in allowed_types:
            errors["type"] = f"Notification type must be one of: {', '.join(allowed_types)}."
            
        if "status" in data and not is_valid_status(data.get("status")):
            errors["status"] = "Status must be 'active' or 'inactive'."
            
        return len(errors) == 0, errors

