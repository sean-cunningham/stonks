# SPY 0DTE Micro-Impulse Scalper — Strategy 2 isolation

## Strategy 1 touchpoints (do not change behavior)

| Area | Location | Role |
|------|----------|------|
| Scheduler | `backend/app/jobs/scheduler.py` | `market_job` → `run_market_tick` (45s), `recon_job` → `run_reconciliation_tick` (300s) |
| Main loop | `backend/app/jobs/market_loop.py` | Candidates, approvals, Strategy-1 pipeline |
| Reconciliation | `backend/app/jobs/reconciliation_loop.py` | Reads/writes `active_positions` only |
| Ledger | `active_positions`, `approved_trades`, `candidate_trades`, `fills` | Strategy-1 paper ledger |
| Bot pause | `bot_states` (id=1) via `BotStateRepository` | Strategy-1 only |

## Scalper isolation

- **Tables**: `strategy_bot_states`, `spy_scalper_candidate_events`, `spy_scalper_positions`, `spy_scalper_fills`, `spy_scalper_daily_summaries`. No rows in Strategy-1 tables for scalper trades.
- **Reconciliation**: `backend/app/jobs/spy_scalper_reconciliation_loop.py` runs on its own scheduler interval and touches only `spy_scalper_positions` / fills / summaries.
- **Runtime**: `backend/app/strategies/spy_0dte_scalper/` — separate config namespace (`SPY_SCALPER_*` in `Settings`), paper execution path, metrics keyed by slug `spy-0dte-scalper`.

## Shared infrastructure (read-only reuse)

- `SessionLocal`, `get_settings()`, market data (`QuoteCache`, broker adapters), logging, auth patterns for new routers.
