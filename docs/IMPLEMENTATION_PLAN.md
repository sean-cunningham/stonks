# Implementation plan

## Completed phases
1. Config / env, database models, Alembic migrations.
2. Provider and AI wiring (OpenAI primary, xAI enrichment, optional TheNewsAPI).
3. Setup-library strategy, fusion, risk, trade management, reconciliation.
4. API, frontend dashboard, tests, baseline docs.

## Controlled learning analytics (current)
1. **Persistence:** `trade_reviews`, `setup_performance_snapshots`, `recommendation_items`, `parameter_experiment_results`; position water marks and R-milestone flags for MFE/MAE and hit rates.
2. **Close path:** reconciliation updates marks, milestones, and journals a review via `TradeReviewService`; exit classifier and shadow experiments attach to the review.
3. **Analytics services:** grouped metrics, recommendation generator (human review only), shadow experiment helper.
4. **API:** `/analytics/*` routes; `analytics_compact` on `/status`.
5. **Frontend:** setup table, exit-quality and family comparison, recommendations panel, trade-review modal.
6. **Tests / docs:** analytics math, classifier, shadow, recommendations, API contracts; governance language in README and docs.
