import os
import json
import sqlite3

from flask import Flask, jsonify
import redis

app = Flask(__name__)

DB_PATH = '/app/data/app.db'

redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    password=os.environ.get('REDIS_PASSWORD', 'defaultpass'),
    db=0,
    decode_responses=True,
    socket_connect_timeout=2
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/api/health')
def health():
    checks = {}

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='pipeline_runs'"
        )
        table_exists = cursor.fetchone()[0] > 0
        conn.close()
        checks['database'] = 'ok' if table_exists else 'error: table not found'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'

    try:
        redis_client.ping()
        checks['cache'] = 'ok'
    except Exception as e:
        checks['cache'] = f'error: {str(e)}'

    all_ok = all(v == 'ok' for v in checks.values())
    status = 'healthy' if all_ok else 'degraded'
    return jsonify({'status': status, 'checks': checks}), 200 if all_ok else 503


@app.route('/api/runs')
def get_runs():
    # try cache first
    try:
        cached = redis_client.get('runs_cache')
        if cached:
            return jsonify({'source': 'cache', 'runs': json.loads(cached)})
    except Exception:
        pass

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pipeline_name, status, records_processed, started_at, duration_sec "
            "FROM pipeline_runs"
        )
        runs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        try:
            redis_client.setex('runs_cache', 300, json.dumps(runs))
        except Exception:
            pass

        return jsonify({'source': 'database', 'runs': runs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics')
def get_metrics():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                count(*) as total_runs,
                sum(records_processed) as total_records,
                round(avg(duration_sec), 2) as avg_duration,
                sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs
            FROM pipeline_runs
        """)
        row = dict(cursor.fetchone())
        conn.close()
        return jsonify({'metrics': row})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
