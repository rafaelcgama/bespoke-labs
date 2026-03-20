import sqlite3
import os

DB_PATH = '/app/data/app.db'


def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Seed initial data
    users = [
        (1, 'Alice Johnson', 'alice@example.com', 'admin'),
        (2, 'Bob Smith', 'bob@example.com', 'developer'),
        (3, 'Charlie Brown', 'charlie@example.com', 'analyst'),
        (4, 'Diana Prince', 'diana@example.com', 'developer'),
        (5, 'Eve Wilson', 'eve@example.com', 'manager'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (id, name, email, role) VALUES (?, ?, ?, ?)",
        users
    )
    conn.close()


if __name__ == '__main__':
    init_database()
    print("Database initialized successfully")
