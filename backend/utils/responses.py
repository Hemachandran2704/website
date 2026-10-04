from flask import jsonify

def success_response(data=None, message="Operation successful", status_code=200):
    """
    Standard successful JSON response wrapper.
    """
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }
    return jsonify(payload), status_code


def error_response(message="Operation failed", errors=None, status_code=400):
    """
    Standard error JSON response wrapper.
    """
    payload = {
        "success": False,
        "message": message,
        "errors": errors if errors is not None else {}
    }
    return jsonify(payload), status_code
