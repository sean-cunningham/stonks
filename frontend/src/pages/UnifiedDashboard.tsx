import { useState } from "react";
import { postStrategyDisable, postStrategyEnable } from "@/api/client";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { useStrategyDashboard } from "@/hooks/useStrategyDashboard";
import { getDashboardStrategyUi } from "@/strategies/dashboardUiRegistry";
import { STRATEGY_REGISTRY } from "@/strategies/registry";
import type { StrategyId } from "@/strategies/registry";

const pollMs = Number(import.meta.env.VITE_REFRESH_INTERVAL_MS) || 5000;
const appName = import.meta.env.VITE_APP_NAME || "Stonks";
const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function UnifiedDashboard({ strategyId }: { strategyId: StrategyId }) {
  const meta = STRATEGY_REGISTRY.find((s) => s.id === strategyId)!;
  const { data, error, refresh } = useStrategyDashboard(strategyId, pollMs);
  const [busy, setBusy] = useState<string | null>(null);

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    try {
      await fn();
      refresh();
    } finally {
      setBusy(null);
    }
  }

  const { Extras, HeaderActions } = getDashboardStrategyUi(strategyId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DashboardShell
        title={`${appName} — ${meta.label}`}
        subtitle={meta.description}
        bundle={data}
        error={error}
        busy={busy}
        apiBase={apiBase}
        pollSeconds={pollMs / 1000}
        onEnable={() => run("enable", () => postStrategyEnable(strategyId))}
        onDisable={() => run("disable", () => postStrategyDisable(strategyId))}
        onRefresh={() => refresh()}
        headerActions={
          HeaderActions ? (
            <HeaderActions busy={busy} run={run} />
          ) : undefined
        }
      >
        {Extras ? <Extras bundle={data} /> : null}
      </DashboardShell>
    </div>
  );
}
