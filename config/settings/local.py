"""
Local development settings for QMS Automotive.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

if env("DATABASE_URL", default=None):
    DATABASES = {
        "default": env.db("DATABASE_URL")
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
