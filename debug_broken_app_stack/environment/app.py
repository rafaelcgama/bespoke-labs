import os
import json
import sqlite3

from flask import Flask, jsonify
import redis

app = Flask(__name__)

DB_PATH = '/app/data/app.db'

# Redis configuration
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

    # Check database
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='users'"
        )
        table_exists = cursor.fetchone()[0] > 0
        conn.close()
        checks['database'] = 'ok' if table_exists else 'error'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'

    # Check Redis
    try:
        redis_client.ping()
        checks['cache'] = 'ok'
    except Exception as e:
        checks['cache'] = f'error: {str(e)}'

    all_ok = all(v == 'ok' for v in checks.values())
    status = 'healthy' if all_ok else 'degraded'
    code = 200 if all_ok else 503

    return jsonify({'status': status, 'checks': checks}), code


@app.route('/api/users')
def get_users():
    # Try cache first
    try:
        cached = redis_client.get('users_cache')
        if cached:
            return jsonify({'source': 'cache', 'users': json.loads(cached)})
    except Exception:
        pass

    # Fall back to database
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Cache the result for 5 minutes
        try:
            redis_client.setex('users_cache', 300, json.dumps(users))
        except Exception:
            pass

        return jsonify({'source': 'database', 'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
