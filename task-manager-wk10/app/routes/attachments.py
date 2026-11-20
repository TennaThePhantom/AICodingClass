"""Download files attached to tasks."""

import os

from flask import Blueprint, current_app, send_file

bp = Blueprint("attachments", __name__, url_prefix="/attachments")


@bp.get("/<path:filename>")
def download(filename):
    path = os.path.join(current_app.config["ATTACHMENTS_DIR"], filename)
    if not os.path.isfile(path):
        return {"error": "not found"}, 404
    return send_file(path)
