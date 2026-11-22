"""Application settings."""

import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Secrets come from the environment only. os.environ[...] raises KeyError at import
# if a value is missing, so the app fails closed instead of running with a default.
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]
if not SECRET_KEY or not ADMIN_TOKEN:
    raise RuntimeError("SECRET_KEY and ADMIN_TOKEN must be non-empty")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
