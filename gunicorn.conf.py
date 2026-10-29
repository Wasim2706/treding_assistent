import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Gunicorn configuration file for Render deployment
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
