import { useState } from "react";
import { UnifiedDashboard } from "@/pages/UnifiedDashboard";
import { STRATEGY_EVENT_EDGE_V1, STRATEGY_REGISTRY } from "@/strategies/registry";
import type { StrategyId } from "@/strategies/registry";

export default function App() {
  const [strategyId, setStrategyId] = useState<StrategyId>(STRATEGY_EVENT_EDGE_V1);
  return (
    <div className="min-h-screen bg-slate-950">
      <nav className="border-b border-slate-800 bg-slate-900/90 px-4 py-2">
        <div className="mx-auto flex max-w-7xl flex-wrap gap-2">
          {STRATEGY_REGISTRY.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setStrategyId(s.id)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                strategyId === s.id ? "bg-slate-100 text-slate-900" : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              {s.shortLabel}
            </button>
          ))}
        </div>
      </nav>
      <UnifiedDashboard strategyId={strategyId} key={strategyId} />
    </div>
  );
}
