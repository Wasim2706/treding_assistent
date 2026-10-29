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

# Expose 'app' directly on the package supporting both WSGI and ASGI callers
try:
    from a2wsgi import ASGIMiddleware
    from app.main import app as _fastapi_app

    class _UniversalApp:
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app
            self.wsgi_app = ASGIMiddleware(asgi_app)

        def __call__(self, *args, **kwargs):
            if len(args) == 2:
                return self.wsgi_app(*args, **kwargs)
            return self.asgi_app(*args, **kwargs)

    app = _UniversalApp(_fastapi_app)
except Exception:
    from app.main import app
