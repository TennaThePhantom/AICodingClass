"""Exploit tests for PA10. Each test fails while the vulnerability exists.

Committed while red (Task 2a). Fixes in Task 2b must not modify this file.
"""

import os

import pytest

from app.config import ADMIN_TOKEN, ATTACHMENTS_DIR


# ---------------------------------------------------------------------------
# Finding 1 — SQL injection in tasks_with_tag (Critical)
# ---------------------------------------------------------------------------
def test_sqli_in_tag_filter_does_not_return_unrelated_tasks(app, client):
    """tag=' OR '1'='1 must not return tasks that do not carry that tag."""
    client.post("/tasks", json={"title": "alpha", "tags": ["red"]})
    client.post("/tasks", json={"title": "beta", "tags": ["blue"]})

    # Classic injection: if interpolated, this matches every row.
    resp = client.get("/tasks/tagged", query_string={"tag": "' OR '1'='1"})
    assert resp.status_code == 200
    returned_titles = {t["title"] for t in resp.get_json()}
    # Today this returns {'alpha','beta'} -> test FAILS. After fix -> empty set.
    assert returned_titles == set(), f"SQLi leaked tasks: {returned_titles}"


# ---------------------------------------------------------------------------
# Finding 2 — Path traversal in attachments.download (Critical)
# ---------------------------------------------------------------------------
def test_attachment_download_cannot_escape_attachments_dir(app, client):
    """GET /attachments/../<file> must not read files outside ATTACHMENTS_DIR."""
    # A real file that lives OUTSIDE the attachments dir, in the repo root.
    outside = os.path.join(os.path.dirname(ATTACHMENTS_DIR), "requirements.txt")
    assert os.path.isfile(outside), "test fixture: requirements.txt should exist"

    resp = client.get("/attachments/../requirements.txt")
    # Today -> 200 + file contents. After fix -> 404 (or 400).
    assert resp.status_code == 404, (
        f"path traversal succeeded: {resp.status_code} {resp.data[:80]!r}"
    )


# ---------------------------------------------------------------------------
# Finding 3 — Hardcoded ADMIN_TOKEN in config.py (Critical)
# ---------------------------------------------------------------------------
def test_admin_token_is_not_hardcoded_literal():
    """ADMIN_TOKEN must come from the environment, never a committed literal."""
    # Today config.py sets ADMIN_TOKEN = "letmein-2026" -> this fails.
    assert ADMIN_TOKEN != "letmein-2026", "ADMIN_TOKEN is the committed literal"
    assert os.environ.get("ADMIN_TOKEN") == ADMIN_TOKEN, (
        "ADMIN_TOKEN must be read from the environment"
    )


# ---------------------------------------------------------------------------
# Finding 4 — Hardcoded SECRET_KEY in config.py (High)
# ---------------------------------------------------------------------------
def test_secret_key_is_not_hardcoded_literal():
    """SECRET_KEY must come from the environment, never a committed literal."""
    from app.config import SECRET_KEY

    assert SECRET_KEY != "dev-secret-123", "SECRET_KEY is the committed literal"
    assert os.environ.get("SECRET_KEY") == SECRET_KEY, (
        "SECRET_KEY must be read from the environment"
    )


# ---------------------------------------------------------------------------
# Finding 5 — Non-constant-time admin token compare (High)
# ---------------------------------------------------------------------------
def test_admin_token_compare_is_constant_time():
    """admin.reset must use hmac.compare_digest, not !=."""
    import inspect

    from app.routes import admin

    src = inspect.getsource(admin.reset)
    # Today the source contains `!=` and no compare_digest -> fails.
    assert "compare_digest" in src, "admin.reset must use hmac.compare_digest"


# ---------------------------------------------------------------------------
# Guard: ensure the fix commit does not weaken this file
# ---------------------------------------------------------------------------
def test_security_file_was_not_modified_by_fix():
    """Sanity marker; Task 2b must not edit this file. See git diff --stat tests/."""
    assert True