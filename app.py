import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

backend_app_dir = os.path.join(backend_dir, "app")
__path__ = [backend_app_dir]

from app.main import app as _fastapi_app

app = _fastapi_app
