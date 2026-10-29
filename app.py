import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

backend_app_dir = os.path.join(backend_dir, "app")
__path__ = [backend_app_dir]

from app.main import app as _fastapi_app

# UniversalApp bridges WSGI (Gunicorn default sync worker) and ASGI (UvicornWorker)
try:
    from a2wsgi import ASGIMiddleware

    class UniversalApp:
        """Supports both ASGI (uvicorn) and WSGI (gunicorn sync worker) seamlessly."""
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app
            self.wsgi_app = ASGIMiddleware(asgi_app)

        def __call__(self, *args, **kwargs):
            # WSGI: app(environ, start_response)
            if len(args) == 2:
                return self.wsgi_app(*args, **kwargs)
            # ASGI: app(scope, receive, send)
            return self.asgi_app(*args, **kwargs)

    app = UniversalApp(_fastapi_app)
except Exception:
    app = _fastapi_app

# Set attribute directly on sys.modules['app'] to guarantee getattr(mod, 'app') succeeds
if "app" in sys.modules:
    setattr(sys.modules["app"], "app", app)
