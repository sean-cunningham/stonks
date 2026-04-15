# API — V1

## Core
- `GET /health`
- `GET /status`
- `GET /balances`
- `GET /positions`
- `GET /trades`
- `GET /candidates`
- `GET /rejections`
- `GET /event-analyses`
- `GET /x-enrichments`
- `GET /decisions` (deterministic decision snapshots)

## Bot control
- `GET /bot/state`
- `POST /bot/start`
- `POST /bot/stop`
- `POST /bot/paper-reset`

## Tastytrade bootstrap (local dev)
- `GET /auth/tastytrade/login` — starts OAuth login redirect.
- `GET /auth/tastytrade/callback` — exchanges auth code server-side and stores refresh token metadata.
- `GET /auth/tastytrade/accounts` — lists available accounts using stored token flow.
- `POST /auth/tastytrade/select-account` — persists active account and runs broker smoke test (`refresh`, `dxlink token`, `SPY chain`).

## Analytics (read-only governance)
- `GET /analytics/summary`
- `GET /analytics/setups`
- `GET /analytics/symbols`
- `GET /analytics/recommendations`
- `GET /analytics/trades/{approved_trade_id}/review`

## Status payload notes
- Includes recent decisions (`bucket`, `strategy_track`, veto codes, weighted score).
- Includes analytics compact block.
