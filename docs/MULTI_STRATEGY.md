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

## Cleanup pass: consistency and isolation

- Dashboard shell is now strategy-agnostic: strategy-specific actions are injected via `headerActions`, and Event Edge extras are composed from `frontend/src/strategies/event-edge/`.
- Event Edge reset UX now calls `POST /strategies/event-edge-v1/paper-reset` and is explicitly scoped to Event Edge. Global reset remains available at `/bot/paper-reset` for maintenance use.
- Config and daily summary contracts are normalized across strategies:
  - `GET /strategies/{id}/config` -> `{read_only, effective, overrides, notes}`
  - `GET /strategies/{id}/summary/daily` and `/metrics/daily` -> `{strategy_id, trade_day, metrics, details}`
- Scheduler stop/start behavior is isolated at strategy level: enable routes ensure scheduler startup when any strategy is running; disable routes only stop scheduler when all strategies are stopped.
- SPY scalper dashboard no longer mirrors signals into `logs`; it returns an empty list until a dedicated scalper log feed is added.

## Remaining rough edges

- Account cash is still a shared paper account model; per-strategy cash partitions are not introduced in this pass.
- Scheduler remains globally instantiated with per-job gating; per-strategy scheduler instances are deferred.
- Trade-review route remains Event Edge global under `/analytics/trades/{id}/review`; strategy aliasing is deferred.
