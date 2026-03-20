# Fix the Broken Application Stack

After a recent infrastructure update, the company's internal API has stopped working. The application stack consists of:

- **Nginx** as a reverse proxy (config at `/etc/nginx/sites-available/default`)
- **Gunicorn** serving a Flask API application (config at `/app/gunicorn_config.py`)
- **Redis** for caching (config at `/etc/redis/redis.conf`)
- **SQLite** for data persistence (database at `/app/data/app.db`)
- **supervisord** managing all processes (config at `/etc/supervisor/conf.d/app.conf`)

All application source files are located in `/app/`.

## Your Task

Diagnose and fix all issues preventing the application from working correctly. The system has multiple configuration and code problems that need to be resolved. You will need to carefully analyze logs, compare configurations across components, and understand how the services interact with each other.

## Success Criteria

Once all issues are fixed, the following must work:

1. `curl http://localhost/api/health` must return HTTP 200 with a JSON response showing:
   - `"status": "healthy"`
   - All component checks (`database` and `cache`) showing `"ok"`

2. `curl http://localhost/api/users` must return HTTP 200 with all 5 seeded users, each having `id`, `name`, `email`, and `role` fields.

3. Redis caching must be functional — subsequent requests to `/api/users` should return data sourced from the cache.

4. The database initialization script (`/app/init_db.py`) must correctly persist data when executed.

## Where to Look

- Service logs: `/var/log/supervisor/`, `/var/log/nginx/`, `/var/log/gunicorn/`
- Service status: `supervisorctl status`
- Application source: `/app/app.py`, `/app/init_db.py`
- Configuration files: Check each service's config for consistency with others
- After making fixes, restart affected services using `supervisorctl restart <service>` or `nginx -s reload`
