# Fix the Broken Data Pipeline Service

After a recent refactoring, the company's data pipeline monitoring API stopped working. The service consists of:

- **Nginx** as a reverse proxy (config at `/etc/nginx/sites-available/default`)
- **Gunicorn** serving a Flask API (config at `/app/gunicorn_config.py`)
- **Redis** for caching (config at `/etc/redis/redis.conf`)
- **SQLite** for pipeline run data (database at `/app/data/app.db`)
- **Supervisord** managing all processes (config at `/etc/supervisor/conf.d/app.conf`)

All application source files are in `/app/`.

## Your Task

Diagnose and fix all issues preventing the service from working. Multiple things broke during the refactoring — you'll need to compare configurations across different components and trace how the services connect.

## Success Criteria

1. `curl http://localhost/api/health` returns HTTP 200 with `"status": "healthy"` and all checks (`database`, `cache`) showing `"ok"`.

2. `curl http://localhost/api/runs` returns HTTP 200 with 5 pipeline run records, each with `id`, `pipeline_name`, `status`, `records_processed`, `started_at`, and `duration_sec` fields.

3. `curl http://localhost/api/metrics` returns HTTP 200 with aggregated pipeline metrics.

4. Redis caching works — subsequent requests to `/api/runs` should come from cache.

5. The database initialization script (`/app/init_db.py`) must correctly persist data when executed.

## Where to Look

- Service logs: `/var/log/supervisor/`, `/var/log/nginx/`, `/var/log/gunicorn/`
- Service status: `supervisorctl status`
- Application source: `/app/app.py`, `/app/init_db.py`
- Compare configurations across files for consistency
- After making fixes, restart affected services
