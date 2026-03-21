# Bespoke Labs — DevOps Task Submission

A "Hard" difficulty DevOps debugging task for the Harbor Terminal Bench 2.0 framework.

## Task Overview

**Scenario:** A web application stack (Nginx, Gunicorn, Flask, Redis, SQLite) has stopped working after an infrastructure update. The application has 3 configuration and code bugs that prevent it from functioning.

**Your job:** Diagnose and fix all issues so the application works correctly.

## Task Structure

- **`debug_broken_app_stack/`** — The complete task submission
  - `instruction.md` — Problem statement given to the AI agent
  - `task.toml` — Task metadata and configuration
  - `environment/` — The broken application environment (Docker setup)
  - `solution/` — The golden solution (`solve.sh`)
  - `tests/` — Verification tests (16 pytest tests)

## The 3 Bugs Fixed

1. **Nginx proxy mismatch:** Nginx configured to proxy to `127.0.0.1:8000` but Gunicorn binds to Unix socket `/tmp/gunicorn.sock`
2. **Redis password mismatch:** redis.conf has `S3cure_P@ss2024` (with underscore) but Flask expects `S3cureP@ss2024` (no underscore)
3. **Database not persisting:** init_db.py calls `conn.commit()` after CREATE TABLE but not after INSERT, so seed data is lost

## Solution Verification

Run the oracle test to verify the solution works:
```bash
harbor run -p "./debug_broken_app_stack" -a oracle
```

**Result:** All 16 tests pass (Mean: 1.000)

## Test Coverage

The 16 tests verify:
- ✓ All services running (Nginx, Gunicorn, Redis)
- ✓ Health endpoint returns 200 with healthy status
- ✓ Database and cache checks pass
- ✓ `/api/users` returns all 5 seeded users
- ✓ Redis caching works (second request from cache)
- ✓ Database initialization persists data correctly

## Setup

Requires:
- Docker
- Harbor CLI (`uv tool install harbor`)
- Groq API key (for AI agent testing)
