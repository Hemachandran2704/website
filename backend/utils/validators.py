import re
from urllib.parse import urlparse

# Whitelist of strictly permitted CSS property names
ALLOWED_CSS_PROPERTIES = {
    "font-size",
    "font-weight",
    "color",
    "background-color",
    "border-radius",
    "padding",
    "margin",
    "width",
    "height",
    "opacity",
    "display",
    "text-align"
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DANGEROUS_PROTOCOLS = ("javascript:", "data:", "vbscript:", "file:")
TAG_RE = re.compile(r"<[^>]+>")


def sanitize_input(val):
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)
    # Strip HTML tags
    cleaned = TAG_RE.sub("", val)
    return cleaned.strip()



def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_status(status):
    return status in ("active", "inactive", "disabled")


def is_allowed_css_property(prop):
    if not prop or not isinstance(prop, str):
        return False
    return prop.strip().lower() in ALLOWED_CSS_PROPERTIES


def is_safe_css_value(val):
    if not val or not isinstance(val, str):
        return False
    val_clean = val.strip().lower()
    # Reject expression(), javascript:, url(javascript:), behaviors, or tags
    if any(keyword in val_clean for keyword in ("expression", "javascript", "<", ">", "behavior:", "@import")):
        return False
    return len(val.strip()) > 0 and len(val.strip()) <= 200


def is_safe_url(url):
    """
    Validates URLs to ensure they use safe protocols (http, https) or valid relative paths.
    Explicitly forbids dangerous protocols like javascript: or data:
    """
    if not url or not isinstance(url, str):
        return False
    url_stripped = url.strip().lower()
    for proto in DANGEROUS_PROTOCOLS:
        if url_stripped.startswith(proto):
            return False
            
    # Check if absolute URL or valid local path
    if url_stripped.startswith("http://") or url_stripped.startswith("https://") or url_stripped.startswith("/") or url_stripped.startswith("#"):
        return True
    return False


def is_valid_integer(val, min_val=None, max_val=None):
    try:
        ival = int(val)
        if min_val is not None and ival < min_val:
            return False
        if max_val is not None and ival > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False
