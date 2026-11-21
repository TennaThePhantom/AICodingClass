"""Application settings."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Secrets come from the environment only. os.environ[...] raises KeyError at import
# if a value is missing, so the app fails closed instead of running with a default.
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
