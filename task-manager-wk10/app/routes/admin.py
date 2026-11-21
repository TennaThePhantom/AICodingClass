"""Admin-only maintenance routes."""

import hmac

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import Task

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.post("/reset")
def reset():
    """Delete every task. Used to reset the demo database."""
    # Constant-time compare so response timing doesn't leak how much of the token matched.
    # Compare bytes: compare_digest raises TypeError on non-ASCII str input.
    supplied = request.args.get("token", "").encode()
    expected = current_app.config["ADMIN_TOKEN"].encode()
    if not hmac.compare_digest(supplied, expected):
        return jsonify({"error": "forbidden"}), 403
    deleted = Task.query.delete()
    db.session.commit()
    return jsonify({"deleted": deleted})
