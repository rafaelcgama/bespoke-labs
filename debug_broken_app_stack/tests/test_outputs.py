import pytest
import subprocess
import json
import time


def run_cmd(cmd, timeout=15):
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return result


def curl_with_retry(url, max_retries=5, delay=2):
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

    def test_nginx_is_running(self):
        result = run_cmd("pgrep -x nginx")
        assert result.returncode == 0, "Nginx is not running"

    def test_gunicorn_is_running(self):
        result = run_cmd("pgrep -f gunicorn")
        assert result.returncode == 0, "Gunicorn is not running"

    def test_redis_is_running(self):
        result = run_cmd("pgrep -x redis-server")
        assert result.returncode == 0, "Redis is not running"


class TestHealthEndpoint:

    def test_health_returns_200(self):
        body, status = curl_with_retry("http://localhost/api/health")
        assert status == 200, f"Expected 200, got {status}"

    def test_health_status_is_healthy(self):
        body, status = curl_with_retry("http://localhost/api/health")
        assert body is not None, "No response from health endpoint"
        data = json.loads(body)
        assert data['status'] == 'healthy', (
            f"Status is '{data['status']}', checks: {data.get('checks')}"
        )

    def test_health_database_ok(self):
        body, _ = curl_with_retry("http://localhost/api/health")
        data = json.loads(body)
        assert data['checks']['database'] == 'ok', (
            f"Database check: {data['checks']['database']}"
        )

    def test_health_cache_ok(self):
        body, _ = curl_with_retry("http://localhost/api/health")
        data = json.loads(body)
        assert data['checks']['cache'] == 'ok', (
            f"Cache check: {data['checks']['cache']}"
        )


class TestRunsEndpoint:

    def test_runs_returns_200(self):
        body, status = curl_with_retry("http://localhost/api/runs")
        assert status == 200, f"Expected 200, got {status}"

    def test_runs_returns_five_records(self):
        body, _ = curl_with_retry("http://localhost/api/runs")
        data = json.loads(body)
        assert len(data['runs']) == 5, (
            f"Expected 5 runs, got {len(data['runs'])}"
        )

    def test_runs_have_required_fields(self):
        body, _ = curl_with_retry("http://localhost/api/runs")
        data = json.loads(body)
        required = {'id', 'pipeline_name', 'status', 'records_processed',
                     'started_at', 'duration_sec'}
        for run in data['runs']:
            missing = required - set(run.keys())
            assert not missing, f"Run {run} missing fields: {missing}"

    def test_user_import_pipeline_exists(self):
        body, _ = curl_with_retry("http://localhost/api/runs")
        data = json.loads(body)
        names = [r['pipeline_name'] for r in data['runs']]
        assert 'user_import' in names, f"user_import not in {names}"

    def test_has_completed_and_failed_runs(self):
        body, _ = curl_with_retry("http://localhost/api/runs")
        data = json.loads(body)
        statuses = set(r['status'] for r in data['runs'])
        assert 'completed' in statuses, f"No completed runs in {statuses}"
        assert 'failed' in statuses, f"No failed runs in {statuses}"


class TestMetricsEndpoint:

    def test_metrics_returns_200(self):
        body, status = curl_with_retry("http://localhost/api/metrics")
        assert status == 200, f"Expected 200, got {status}"

    def test_metrics_total_runs(self):
        body, _ = curl_with_retry("http://localhost/api/metrics")
        data = json.loads(body)
        assert data['metrics']['total_runs'] == 5

    def test_metrics_successful_runs(self):
        body, _ = curl_with_retry("http://localhost/api/metrics")
        data = json.loads(body)
        assert data['metrics']['successful_runs'] == 4


class TestCaching:

    def test_second_request_from_cache(self):
        run_cmd(
            "redis-cli -a \"$(grep requirepass /etc/redis/redis.conf "
            "| sed 's/requirepass //;s/\"//g')\" DEL runs_cache 2>/dev/null"
        )
        curl_with_retry("http://localhost/api/runs")
        time.sleep(1)
        body, status = curl_with_retry("http://localhost/api/runs")
        assert status == 200
        data = json.loads(body)
        assert data['source'] == 'cache', (
            f"Expected 'cache', got '{data['source']}'"
        )


class TestDatabaseInit:

    def test_init_persists_data(self):
        run_cmd("rm -f /app/data/app.db")
        result = run_cmd("cd /app && python3 init_db.py")
        assert result.returncode == 0, f"init_db failed: {result.stderr}"
        verify = run_cmd(
            "python3 -c \""
            "import sqlite3; "
            "conn = sqlite3.connect('/app/data/app.db'); "
            "cursor = conn.cursor(); "
            "cursor.execute('SELECT count(*) FROM pipeline_runs'); "
            "count = cursor.fetchone()[0]; "
            "conn.close(); "
            "print(count)\""
        )
        count = int(verify.stdout.strip())
        assert count == 5, f"Expected 5 runs persisted, got {count}"

    def test_init_creates_correct_schema(self):
        run_cmd("rm -f /app/data/app.db")
        run_cmd("cd /app && python3 init_db.py")
        verify = run_cmd(
            "python3 -c \""
            "import sqlite3; "
            "conn = sqlite3.connect('/app/data/app.db'); "
            "cursor = conn.cursor(); "
            "cursor.execute('PRAGMA table_info(pipeline_runs)'); "
            "cols = [row[1] for row in cursor.fetchall()]; "
            "conn.close(); "
            "print(','.join(cols))\""
        )
        columns = verify.stdout.strip().split(',')
        assert 'id' in columns
        assert 'pipeline_name' in columns
        assert 'status' in columns
        assert 'records_processed' in columns
