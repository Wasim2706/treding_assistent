import os

# Gunicorn configuration file for Render deployment
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
