# API

## Health & status
- `GET /health` — liveness.
- `GET /status` — bot state, balances, recent entities, **analytics_compact** (win rate, expectancy preview, exit-quality top, governance note).

## Analytics (read-only learning)
- `GET /analytics/summary` — overall metrics, exit-quality counts, top reason codes, anticipatory vs confirmed slices, governance note.
- `GET /analytics/setups` — per–setup-type performance rows.
- `GET /analytics/symbols` — per-symbol performance rows.
- `GET /analytics/recommendations?refresh=true|false` — stored suggestions for human review; `refresh=true` may append new rows from latest stats.
- `GET /analytics/trades/{trade_id}/review` — **trade_id** = `approved_trades.id`; full journal + shadow experiments, or 404 if not closed/journaled.

## Operations
- `GET /balances`, `GET /positions`, `GET /trades`, `GET /event-analyses`, `GET /x-enrichments`, `GET /candidates`, `GET /rejections`.
- `GET /bot/state`, `POST /bot/start`, `POST /bot/stop`, `POST /bot/paper-reset` — reset clears analytics tables along with trading history.

## Field notes
- Status and positions include trade-management and **MFE/MAE water-mark** fields on open positions.
- Candidates and event analyses expose setup scoring and reason codes.
