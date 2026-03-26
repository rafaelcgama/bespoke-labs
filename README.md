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
  - `tests/` — Verification tests (18 pytest tests)

## The 3 Bugs Fixed

1. **Nginx proxy mismatch:** Nginx configured to proxy to `127.0.0.1:8000` but Gunicorn binds to `0.0.0.0:5000`
2. **Database path mismatch:** `init_db.py` writes to `/app/data/pipeline.db` but `app.py` reads from `/app/data/app.db`
3. **Missing Redis password:** Supervisord config doesn't pass `REDIS_PASSWORD` env var to Gunicorn, so Flask can't authenticate with Redis

## Solution Verification

Run the oracle test to verify the solution works:
```bash
harbor run -p "./debug_broken_app_stack" -a oracle
```

**Result:** All 18 tests pass (Mean: 1.000)

## Test Coverage

The 18 tests verify:
- ✓ All services running (Nginx, Gunicorn, Redis)
- ✓ Health endpoint returns 200 with healthy status
- ✓ Database and cache checks pass
- ✓ `/api/runs` returns all 5 seeded pipeline runs
- ✓ `/api/metrics` returns aggregated pipeline metrics
- ✓ Redis caching works (second request from cache)
- ✓ Database initialization persists data correctly

## Setup

Requires:
- Docker
- Harbor CLI (`uv tool install harbor`)
- Groq API key (for AI agent testing)
