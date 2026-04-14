# Event Edge Bot 2k
OpenAI primary via Responses; xAI optional sidecar; TheNewsAPI optional supplemental feed.

**Learning / analytics:** post-trade journaling, grouped metrics, exit-quality labels, human-review recommendations, and offline shadow experiments are **read-only**. They do **not** auto-change live strategy, risk, or execution. Adopt any parameter or rule change only after human review and replay/paper validation.

Copy .env.example to backend/.env and never commit .env.
Run backend: install deps, alembic upgrade head, uvicorn app.main:app --reload.
Run frontend: npm install, npm run dev.
Modes: mock, market_data, full_analysis.
Tests: py -m pytest tests/ -q
