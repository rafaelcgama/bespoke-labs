import multiprocessing

# Server socket
bind = "unix:/tmp/gunicorn.sock"

# Worker processes
workers = 2
worker_class = "sync"
timeout = 30

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
