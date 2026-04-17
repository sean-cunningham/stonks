# Multi-strategy architecture (refactor baseline)

## Single-strategy touchpoints (legacy)

- **HTTP**: Strategy A uses flat routes (`/status`, `/bot/*`, `/candidates`, …). Scalper historically used `/strategies/spy-0dte-scalper/*` only.
- **State**: `bot_states.id=1` (Strategy A) vs `strategy_bot_states.strategy_slug` (scalper).
- **Scheduler**: Separate hard-coded jobs for `market_loop` / recon vs `spy_scalper_*` ticks.
- **UI**: Previously swapped two full pages (`Dashboard` vs `SpyScalperDashboard`) instead of one shell.

## Non-goals (do not violate)

- Do **not** change Strategy A decision logic inside `market_loop`, `approval_engine`, or `candidate_generator`.
- Do **not** merge ledgers: scalper stays on `spy_scalper_*` tables; Strategy A on `active_positions` / `approved_trades` / etc.

## Canonical strategy IDs

- `event-edge-v1` — Event Edge Bot (Strategy A)
- `spy-0dte-scalper` — SPY 0DTE Micro-Impulse Scalper

All strategy-scoped APIs live under `/strategies/{strategy_id}/...` with a shared dashboard DTO where possible.
