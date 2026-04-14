# Stonks backend

Python package under `app/`. See root [README.md](../README.md) for full project docs.

```bash
cd backend
py -m pip install -e ".[dev]"
py -m alembic upgrade head
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Seed demo data:

```bash
py -m scripts.seed_demo
```

Tests:

```bash
py -m pytest tests/ -q
```
