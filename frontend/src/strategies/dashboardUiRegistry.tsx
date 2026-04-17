import type { ComponentType } from "react";
import { EventEdgeDashboardExtras, EventEdgeHeaderActions } from "@/strategies/event-edge/EventEdgeDashboardExtras";
import { SpyScalperDashboardExtras, SpyScalperHeaderActions } from "@/strategies/spy-0dte-scalper/SpyScalperDashboardExtras";
import type { StrategyId } from "@/strategies/registry";
import { STRATEGY_EVENT_EDGE_V1, STRATEGY_SPY_0DTE_SCALPER } from "@/strategies/registry";
import type { StrategyDashboardBundleRead } from "@/types/api";

export type DashboardHeaderActionsProps = {
  busy: string | null;
  run: (label: string, fn: () => Promise<unknown>) => Promise<void>;
};

export type DashboardExtrasProps = {
  bundle: StrategyDashboardBundleRead | null;
};

type StrategyUiEntry = {
  HeaderActions?: ComponentType<DashboardHeaderActionsProps>;
  Extras?: ComponentType<DashboardExtrasProps>;
};

const STRATEGY_DASHBOARD_UI: Record<StrategyId, StrategyUiEntry> = {
  [STRATEGY_EVENT_EDGE_V1]: {
    HeaderActions: EventEdgeHeaderActions,
    Extras: EventEdgeDashboardExtras,
  },
  [STRATEGY_SPY_0DTE_SCALPER]: {
    HeaderActions: SpyScalperHeaderActions,
    Extras: SpyScalperDashboardExtras,
  },
};

export function getDashboardStrategyUi(strategyId: StrategyId): StrategyUiEntry {
  return STRATEGY_DASHBOARD_UI[strategyId] ?? {};
}
