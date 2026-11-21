"""Download files attached to tasks."""

import os

from flask import Blueprint, current_app, send_file

bp = Blueprint("attachments", __name__, url_prefix="/attachments")


@bp.get("/<path:filename>")
def download(filename):
    """Send an attachment, refusing any path that resolves outside ATTACHMENTS_DIR."""
    base = os.path.realpath(current_app.config["ATTACHMENTS_DIR"])
    path = os.path.realpath(os.path.join(base, filename))
    try:
        inside = os.path.commonpath([base, path]) == base
    except ValueError:
        # Different drives on Windows (e.g. an absolute "D:/..." filename).
        inside = False
    if not inside or not os.path.isfile(path):
        return {"error": "not found"}, 404
    return send_file(path)
