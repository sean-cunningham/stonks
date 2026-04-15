# Trading Rules — V1

## Scope
- ETF universe only: SPY, QQQ, IWM, XLF, XLK, TLT, SLV.
- Intraday only, force flat by 15:30 ET.
- No event-burst auto trading, no overnight auto trades.

## Strategy A (auto-execute eligible)
- Setup families: trend continuation, failed breakout/rejection.
- Hard veto must pass before scoring.
- Minimum reward to first target: 1.5R.
- Contract constraints: DTE 7-14, delta 0.50-0.65, strict spread filters.

## Strategy B (recommend-only)
- Outside Strategy A auto boundaries (e.g., overnight, event-volatility, unsupported structures).
- Subject to recommendation quotas and payload discipline.

## Classification thresholds
- AUTO_EXECUTE: weighted >= 30 and category floors satisfied, Strategy A only.
- RECOMMEND_ONLY: weighted >= 23 with floor checks and at least one recommend driver.
- REJECT: otherwise.

## Governance
- Recommendations are suggested changes for human review only.
- No autonomous parameter/rule adaptation in live flow.
