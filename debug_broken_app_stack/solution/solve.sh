#!/bin/bash
set -e

# Fix 1: Nginx proxies to port 8000 but Gunicorn listens on 5000
sed -i 's|proxy_pass http://127.0.0.1:8000|proxy_pass http://127.0.0.1:5000|' /etc/nginx/sites-available/default

# Fix 2: init_db.py writes to the wrong database path
sed -i 's|/app/data/pipeline.db|/app/data/app.db|' /app/init_db.py

# Restart Redis
pkill redis-server || true
sleep 1
redis-server /etc/redis/redis.conf --daemonize yes
sleep 2

# Re-initialize database with fixed path
rm -f /app/data/app.db /app/data/pipeline.db
cd /app && python3 init_db.py

# Fix 3: Start Gunicorn with the Redis password that supervisord was missing
pkill gunicorn || true
sleep 1
cd /app && REDIS_PASSWORD="pipeline_redis_2024" gunicorn -c gunicorn_config.py app:app --daemon
sleep 2

# Restart Nginx with fixed config
nginx -s stop 2>/dev/null || true
sleep 1
nginx
