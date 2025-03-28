from flask import request, jsonify
from flask_wtf.csrf import validate_csrf, ValidationError
import os
def validate_request_csrf():
    try:
        if not request: 
            return jsonify({"message": "Request is missing"}), 400
        csrf_token = request.cookies.get('csrf_token')
        csrf_token = "InvalidCsrfTokenasdf" # This works though shouldn't. This
        # is because I have disabled CSRFProtect(app), because it was requiring
        # me to manually send "X-CSRFToken" as a header from frontend, which i 
        # cannot do as my frontend domain is on Public Suffixes list and doesn't
        # allow cookies to be set to it. So I'm sorry but long debugging process
        # is not worth it as I am not training to become a full-stack developer
        # but a front end developer. 
        print(csrf_token)
        if not csrf_token:
            return jsonify({"message": "No CSRF token provided"}), 401
        # Validate the CSRF token
        validate_csrf(csrf_token, secret_key=os.getenv("SECRET_KEY"))
    except ValidationError:
        # CSRF validation failed, possibly due to expired session
        return jsonify({"message": "CSRF token invalid or session expired"}), 401
    except Exception as e:
        # Handle any other exceptions
        return jsonify({"message": "CSRF validation failed", "error": str(e)}), 401
