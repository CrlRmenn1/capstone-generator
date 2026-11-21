"""JSON API used by the React frontend. Everything lives under /api."""
from flask import Blueprint, jsonify, request

api = Blueprint("api", __name__, url_prefix="/api")

# State-changing requests must carry this header. Browsers won't send a custom header on a
# cross-site request without a CORS preflight (which we never allow), so this blocks CSRF.
CSRF_HEADER = "X-CapSense"


@api.before_request
def require_csrf_header():
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.headers.get(CSRF_HEADER) != "1":
        return jsonify(error="Missing request header.", code="csrf"), 403
    return None


from . import auth, bookmarks, meta, outlines, settings, titles  # noqa: E402,F401  (register routes)
