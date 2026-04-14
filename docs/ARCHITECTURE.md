# Architecture — Event Edge Bot 2k

## Core pipeline
- **Events:** official-first ingestion; optional TheNewsAPI supplemental headlines (tagged IDs).
- **Primary reasoning:** OpenAI Responses (triage / escalation) produces structured event judgments and setup scores.
- **Optional enrichment:** xAI sidecar for X/social context; gated by limits and allowlists.
- **Strategy:** setup library (bullish/bearish post-event confirmation, anticipatory macro) with scoring, confirmation levels, and cross-market checks for indices.
- **Policy / risk:** fusion checklist and account limits; paper execution with structured trade management (stops, breakeven, partials, trail).

## Controlled learning layer (analytics only)
- **Trade reviews:** on position close, a `trade_review` row captures P&L, R-multiple, MFE/MAE from high/low water marks, hold time, enrichment flags, exit-quality label, and policy snapshot.
- **Analytics engine:** aggregates win rate, expectancy, profit factor, R-milestone rates, exit-quality mix, and slices by setup, symbol, trade family, etc.
- **Recommendations:** `recommendation_item` rows are **suggested for human review**; the execution and policy layers **must not** read or apply them automatically.
- **Shadow experiments:** `parameter_experiment_result` stores offline what-if narratives tied to a review (not executed trades).

## Governance
- No autonomous live adaptation, RL, or self-rewriting production rules driven by this layer.
- Changes to thresholds, stops, or filters require explicit human approval and validation (replay / extended paper).
