"""Admin-only maintenance routes."""

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import Task

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.post("/reset")
def reset():
    """Delete every task. Used to reset the demo database."""
    if request.args.get("token") != current_app.config["ADMIN_TOKEN"]:
        return jsonify({"error": "forbidden"}), 403
    deleted = Task.query.delete()
    db.session.commit()
    return jsonify({"deleted": deleted})
