FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    redis-server \
    supervisor \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask==3.1.0 \
    gunicorn==23.0.0 \
    redis==5.2.1

WORKDIR /app
COPY * /app/

RUN mkdir -p /var/log/gunicorn /var/log/redis /app/data && \
    cp /app/nginx.conf /etc/nginx/sites-available/default && \
    cp /app/redis.conf /etc/redis/redis.conf && \
    cp /app/supervisord.conf /etc/supervisor/conf.d/app.conf

EXPOSE 80

CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
