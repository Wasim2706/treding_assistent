"""
Trading Assistant Backend Application Package
"""
import os
import sys

# Ensure the backend directory containing 'app' is always in sys.path
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

__version__ = "1.0.0"

# Expose 'app' directly on the package so 'gunicorn app:app' or 'getattr(mod, "app")' always succeeds!
from app.main import app
