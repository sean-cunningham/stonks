import { useState } from "react";
import { Dashboard } from "@/pages/Dashboard";
import { SpyScalperDashboard } from "@/pages/SpyScalperDashboard";

type Tab = "strategy1" | "spy_scalper";

export default function App() {
  const [tab, setTab] = useState<Tab>("strategy1");
  return (
    <div className="min-h-screen bg-slate-950">
      <nav className="border-b border-slate-800 bg-slate-900/90 px-4 py-2">
        <div className="mx-auto flex max-w-7xl gap-2">
          <button
            type="button"
            onClick={() => setTab("strategy1")}
            className={`rounded px-3 py-1.5 text-sm font-medium ${
              tab === "strategy1" ? "bg-slate-100 text-slate-900" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            Strategy 1
          </button>
          <button
            type="button"
            onClick={() => setTab("spy_scalper")}
            className={`rounded px-3 py-1.5 text-sm font-medium ${
              tab === "spy_scalper" ? "bg-slate-100 text-slate-900" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            SPY 0DTE scalper
          </button>
        </div>
      </nav>
      {tab === "strategy1" ? <Dashboard /> : <SpyScalperDashboard />}
    </div>
  );
}
