# Trading rules (V1)

## Setups
- `bullish_post_event_confirmation`, `bearish_post_event_confirmation`, `anticipatory_macro_event` (macro event type only for anticipatory).

## Risk
- 3% max risk per trade, 5% daily loss, 8% weekly loss (paper account metrics).
- Structure-based stops with breakeven move, partial profit, and trailing logic.

## Learning and analytics
- Completed trades are journaled for **analysis and review only**.
- **Recommendations and shadow experiments do not alter live behavior.** Operators may use them to propose changes; any change must be coded and deployed deliberately after validation.
