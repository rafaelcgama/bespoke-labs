import sqlite3
import os

DB_PATH = '/app/data/pipeline.db'


def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY,
            pipeline_name TEXT NOT NULL,
            status TEXT NOT NULL,
            records_processed INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            duration_sec REAL NOT NULL
        )
    ''')

    runs = [
        (1, 'user_import', 'completed', 15420, '2024-01-15 08:00:00', 145.3),
        (2, 'transaction_sync', 'completed', 89200, '2024-01-15 09:30:00', 312.7),
        (3, 'report_generation', 'completed', 3200, '2024-01-15 14:00:00', 67.8),
        (4, 'data_cleanup', 'failed', 0, '2024-01-16 02:00:00', 5.2),
        (5, 'user_import', 'completed', 16100, '2024-01-16 08:00:00', 152.1),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO pipeline_runs VALUES (?, ?, ?, ?, ?, ?)",
        runs
    )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_database()
    print("Database initialized")
