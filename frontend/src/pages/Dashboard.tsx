import { UnifiedDashboard } from "@/pages/UnifiedDashboard";
import { STRATEGY_EVENT_EDGE_V1 } from "@/strategies/registry";

/** Back-compat wrapper defaulting to Strategy A. Prefer App + UnifiedDashboard. */
export function Dashboard() {
  return <UnifiedDashboard strategyId={STRATEGY_EVENT_EDGE_V1} />;
}
