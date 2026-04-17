export const STRATEGY_EVENT_EDGE_V1 = "event-edge-v1" as const;
export const STRATEGY_SPY_0DTE_SCALPER = "spy-0dte-scalper" as const;

export type StrategyId = typeof STRATEGY_EVENT_EDGE_V1 | typeof STRATEGY_SPY_0DTE_SCALPER;

export const STRATEGY_REGISTRY: {
  id: StrategyId;
  label: string;
  shortLabel: string;
  description: string;
}[] = [
  {
    id: STRATEGY_EVENT_EDGE_V1,
    label: "Event Edge (Strategy A)",
    shortLabel: "Strategy A",
    description: "ETF options pipeline with approval engine and learning analytics.",
  },
  {
    id: STRATEGY_SPY_0DTE_SCALPER,
    label: "SPY 0DTE Micro-Impulse Scalper",
    shortLabel: "SPY 0DTE scalper",
    description: "Isolated SPY 0DTE paper scalper with its own ledger.",
  },
];
