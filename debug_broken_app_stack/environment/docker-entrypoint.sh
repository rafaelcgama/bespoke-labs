#!/bin/bash
set -e

# Start Redis
redis-server /etc/redis/redis.conf --daemonize yes

# Wait for Redis to start
sleep 1

# Initialize the database
cd /app
python3 init_db.py

# Start Gunicorn
cd /app
gunicorn -c gunicorn_config.py app:app --daemonize

# Wait for Gunicorn to start
sleep 1

# Start Nginx
/usr/sbin/nginx -c /etc/nginx/nginx.conf

# Keep container running
tail -f /dev/null
