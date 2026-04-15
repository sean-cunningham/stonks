# Architecture — Event Edge Bot 2k v1

## Decision pipeline
- Ingest market/events/account inputs.
- Normalize and freshness-check data.
- Compute deterministic 1m/5m/15m feature set.
- Apply context outputs (primary + adversarial) through deterministic arbiter.
- Persist decision snapshot.
- Run hard veto layer before scoring.
- Score survivors and classify to `AUTO_EXECUTE`, `RECOMMEND_ONLY`, or `REJECT`.
- Execute only Strategy A `AUTO_EXECUTE` signals.

## Strategy split
- Strategy A (auto): trend continuation and failed breakout/rejection families.
- Strategy B (recommend-only): any attractive idea outside Strategy A auto constraints (event-vol, overnight, noncompliant risk/contract constraints).

## Risk and execution defaults
- Risk tiers: 1.0% / 1.5% / 2.0%.
- Max 1 open position per symbol, 2 total, 3% combined open risk during launch.
- Stop new entries at 3 losses/day or drawdown stop.
- Limit-at-mid, one improvement, chase caps, no endless chasing.

## Context behavior
- OpenAI context is advisory only.
- Deterministic arbiter can: do nothing, reduce size, require extra confirmation, or block.
- Context cannot create trades or override hard risk rules.

## Replay/observability
- Every evaluation persists a `decision_snapshot` with veto reasons, score card, bucket decision, and order intent.
- Post-trade journal and analytics remain read-only governance tools.
