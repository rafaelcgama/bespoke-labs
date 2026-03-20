FROM python:3.12-slim-bookworm

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    redis-server \
    curl \
    procps \
    systemctl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages with pinned versions
RUN pip install --no-cache-dir \
    flask==3.1.0 \
    gunicorn==23.0.0 \
    redis==5.2.1 \
    pytest==7.4.3

WORKDIR /app

# Copy all environment files into /app/
COPY * /app/

# Create required log and data directories
RUN mkdir -p /var/log/gunicorn /var/log/redis /app/data && \
    chmod 755 /var/log/gunicorn /var/log/redis /app/data

# Deploy configurations to system locations
RUN cp /app/nginx.conf /etc/nginx/sites-available/default && \
    cp /app/redis.conf /etc/redis/redis.conf

EXPOSE 80

# Default command for interactive use
CMD ["/bin/bash"]
