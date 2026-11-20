"""Application settings."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "dev-secret-123"
ADMIN_TOKEN = "letmein-2026"
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
