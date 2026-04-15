# Event Edge Bot 2k

Deterministic intraday ETF options bot with three decision buckets:
- `AUTO_EXECUTE` (Strategy A only)
- `RECOMMEND_ONLY` (Strategy B / outside auto constraints)
- `REJECT`

Core pipeline:
`ingest -> normalize -> feature generation -> context filtering -> decision snapshot -> hard veto -> scoring -> classify -> execute/recommend/reject`

V1 guardrails:
- ETF-only universe: `SPY, QQQ, IWM, XLF, XLK, TLT, SLV`
- intraday only, force flat by `15:30 ET`
- hard veto rules run before scoring
- OpenAI is context-only, deterministic arbiter decides action
- xAI sidecar code remains but runtime-disabled by default (`V1_DISABLE_XAI_RUNTIME=true`)

Learning/analytics:
- Post-trade analytics and recommendations are **human-review only**.
- No autonomous live strategy mutation.

Run:
- backend: `alembic upgrade head` then `uvicorn app.main:app --reload`
- frontend: `npm install && npm run dev`
- tests: `py -m pytest tests/ -q`
