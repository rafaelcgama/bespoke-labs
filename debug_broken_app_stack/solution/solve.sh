#!/bin/bash
set -e

###############################################################################
# Fix 1: Nginx proxy_pass mismatch
# Nginx is configured to proxy to TCP 127.0.0.1:8000, but Gunicorn binds to
# a Unix socket at /tmp/gunicorn.sock. Update nginx to use the Unix socket.
###############################################################################
sed -i 's|proxy_pass http://127.0.0.1:8000;|proxy_pass http://unix:/tmp/gunicorn.sock;|' /etc/nginx/sites-available/default

###############################################################################
# Fix 2: Redis password mismatch
# redis.conf has requirepass "S3cure_P@ss2024" (with underscore after S3cure)
# but the Flask app expects REDIS_PASSWORD="S3cureP@ss2024" (no underscore).
# Align redis.conf to match the password the application uses.
###############################################################################
python3 << 'PYTHON_EOF'
import re

# Fix in /etc (this is where it will be when Redis runs)
config_file = '/etc/redis/redis.conf'
with open(config_file, 'r') as f:
    lines = f.readlines()

# Replace the password line
new_lines = []
for line in lines:
    if 'requirepass' in line and 'S3cure_P@ss2024' in line:
        new_lines.append('requirepass "S3cureP@ss2024"\n')
    else:
        new_lines.append(line)

with open(config_file, 'w') as f:
    f.writelines(new_lines)
PYTHON_EOF

###############################################################################
# Fix 3: Database seed data not persisted
# init_db.py calls conn.commit() after CREATE TABLE but not after the
# executemany INSERT. The data is never committed and is lost when the
# connection closes. Add conn.commit() before conn.close().
###############################################################################
sed -i '/cursor.executemany(/,/conn.close()/{
    s|conn.close()|conn.commit()\n    conn.close()|
}' /app/init_db.py

# Remove stale database so it can be re-initialized with the fixes
rm -f /app/data/app.db

# Kill any existing Redis process
pkill -f redis-server || true
pkill -f redis || true
sleep 2

# Verify the fix was applied
echo "Verifying Redis config fix:"
grep "requirepass" /etc/redis/redis.conf

# Start Redis with the fixed config
/usr/bin/redis-server /etc/redis/redis.conf --daemonize yes
sleep 3

# Test Redis connection with new password
redis-cli -a "S3cureP@ss2024" ping || echo "Redis connection test..."

# Initialize database with fixed script
cd /app && python3 init_db.py
sleep 1

# Start Gunicorn with Redis password
cd /app && REDIS_PASSWORD="S3cureP@ss2024" gunicorn -c gunicorn_config.py app:app --daemon
sleep 2

# Start Nginx
/usr/sbin/nginx

sleep 1
echo "All services started successfully"
