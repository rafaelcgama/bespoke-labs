import pytest
import subprocess
import json
import time


def run_cmd(cmd, timeout=15):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return result


def curl_with_retry(url, max_retries=5, delay=2):
    """Curl a URL with retries, returning (body, status_code)."""
    for i in range(max_retries):
        try:
            result = run_cmd(
                f"curl -s -w '\\n%{{http_code}}' {url}"
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().rsplit('\n', 1)
                if len(lines) == 2:
                    body, status = lines
                    if status != '000':
                        return body, int(status)
        except Exception:
            pass
        time.sleep(delay)
    return None, 0


class TestServicesRunning:
    """Verify all services are running."""

    def test_nginx_is_running(self):
        result = run_cmd("pgrep -x nginx")
        assert result.returncode == 0, "Nginx process is not running"

    def test_gunicorn_is_running(self):
        result = run_cmd("pgrep -f gunicorn")
        assert result.returncode == 0, "Gunicorn process is not running"

    def test_redis_is_running(self):
        result = run_cmd("pgrep -x redis-server")
        assert result.returncode == 0, "Redis server process is not running"


class TestHealthEndpoint:
    """Verify the /api/health endpoint works correctly."""

    def test_health_returns_200(self):
        body, status = curl_with_retry("http://localhost/api/health")
        assert status == 200, f"Health endpoint returned HTTP {status}, expected 200"

    def test_health_status_is_healthy(self):
        body, status = curl_with_retry("http://localhost/api/health")
        assert body is not None, "Health endpoint returned no response"
        data = json.loads(body)
        assert data['status'] == 'healthy', (
            f"Health status is '{data['status']}', expected 'healthy'. "
            f"Checks: {data.get('checks', {})}"
        )

    def test_health_database_check_ok(self):
        body, _ = curl_with_retry("http://localhost/api/health")
        data = json.loads(body)
        assert data['checks']['database'] == 'ok', (
            f"Database check failed: {data['checks']['database']}"
        )

    def test_health_cache_check_ok(self):
        body, _ = curl_with_retry("http://localhost/api/health")
        data = json.loads(body)
        assert data['checks']['cache'] == 'ok', (
            f"Cache check failed: {data['checks']['cache']}"
        )


class TestUsersEndpoint:
    """Verify the /api/users endpoint returns correct data."""

    def test_users_returns_200(self):
        body, status = curl_with_retry("http://localhost/api/users")
        assert status == 200, f"Users endpoint returned HTTP {status}, expected 200"

    def test_users_returns_nonempty_list(self):
        body, _ = curl_with_retry("http://localhost/api/users")
        data = json.loads(body)
        assert len(data['users']) > 0, "Users endpoint returned an empty list"

    def test_users_returns_exactly_five(self):
        body, _ = curl_with_retry("http://localhost/api/users")
        data = json.loads(body)
        assert len(data['users']) == 5, (
            f"Expected 5 users, got {len(data['users'])}"
        )

    def test_users_have_required_fields(self):
        body, _ = curl_with_retry("http://localhost/api/users")
        data = json.loads(body)
        required_fields = {'id', 'name', 'email', 'role'}
        for user in data['users']:
            missing = required_fields - set(user.keys())
            assert not missing, f"User {user} missing fields: {missing}"

    def test_alice_johnson_exists(self):
        body, _ = curl_with_retry("http://localhost/api/users")
        data = json.loads(body)
        names = [u['name'] for u in data['users']]
        assert 'Alice Johnson' in names, (
            f"Alice Johnson not found. Users: {names}"
        )

    def test_admin_role_exists(self):
        body, _ = curl_with_retry("http://localhost/api/users")
        data = json.loads(body)
        roles = [u['role'] for u in data['users']]
        assert 'admin' in roles, f"No admin role found. Roles: {roles}"


class TestRedisCaching:
    """Verify Redis caching is functional."""

    def test_second_request_served_from_cache(self):
        # Clear any existing cache
        run_cmd(
            "redis-cli -a \"$(grep requirepass /etc/redis/redis.conf "
            "| sed 's/requirepass //;s/\"//g')\" DEL users_cache 2>/dev/null"
        )
        # First request populates cache from database
        curl_with_retry("http://localhost/api/users")
        time.sleep(1)
        # Second request should come from cache
        body, status = curl_with_retry("http://localhost/api/users")
        assert status == 200
        data = json.loads(body)
        assert data['source'] == 'cache', (
            f"Expected 'cache' source on second request, got '{data['source']}'"
        )


class TestDatabaseInitScript:
    """Verify that init_db.py correctly persists data."""

    def test_init_db_persists_data(self):
        # Remove existing database
        run_cmd("rm -f /app/data/app.db")
        # Run init_db.py
        result = run_cmd("cd /app && python3 init_db.py")
        assert result.returncode == 0, f"init_db.py failed: {result.stderr}"
        # Verify data is actually persisted (new connection)
        verify = run_cmd(
            "python3 -c \""
            "import sqlite3; "
            "conn = sqlite3.connect('/app/data/app.db'); "
            "cursor = conn.cursor(); "
            "cursor.execute('SELECT count(*) FROM users'); "
            "count = cursor.fetchone()[0]; "
            "conn.close(); "
            "print(count)\""
        )
        count = int(verify.stdout.strip())
        assert count == 5, (
            f"Expected 5 users persisted after init_db.py, got {count}. "
            "The seed data was likely not committed to the database."
        )

    def test_init_db_creates_correct_schema(self):
        run_cmd("rm -f /app/data/app.db")
        run_cmd("cd /app && python3 init_db.py")
        verify = run_cmd(
            "python3 -c \""
            "import sqlite3; "
            "conn = sqlite3.connect('/app/data/app.db'); "
            "cursor = conn.cursor(); "
            "cursor.execute('PRAGMA table_info(users)'); "
            "cols = [row[1] for row in cursor.fetchall()]; "
            "conn.close(); "
            "print(','.join(cols))\""
        )
        columns = verify.stdout.strip().split(',')
        assert 'id' in columns
        assert 'name' in columns
        assert 'email' in columns
        assert 'role' in columns
