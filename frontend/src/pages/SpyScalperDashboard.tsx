import { useCallback, useState } from "react";
import {
  getSpyScalperConfig,
  getSpyScalperMetricsDaily,
  getSpyScalperSignalsRecent,
  getSpyScalperStatus,
  getSpyScalperSummaryDaily,
  postSpyScalperDisable,
  postSpyScalperEnable,
} from "@/api/client";
import { SectionCard } from "@/components/SectionCard";
import { usePolling } from "@/hooks/usePolling";

const pollMs = Number(import.meta.env.VITE_REFRESH_INTERVAL_MS) || 5000;

export function SpyScalperDashboard() {
  const fetchBundle = useCallback(async () => {
    const [status, metrics, signals, summary, config] = await Promise.all([
      getSpyScalperStatus(),
      getSpyScalperMetricsDaily(),
      getSpyScalperSignalsRecent(),
      getSpyScalperSummaryDaily(),
      getSpyScalperConfig(),
    ]);
    return { status, metrics, signals, summary, config };
  }, []);

  const { data, error, refresh } = usePolling(fetchBundle, pollMs);
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

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-xl font-semibold">SPY 0DTE Micro-Impulse Scalper</h1>
            <p className="text-sm text-slate-400">
              Strategy 2 — isolated paper ledger; refresh {pollMs / 1000}s. Start the main bot scheduler for ticks to
              run.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={!!busy}
              onClick={() => run("enable", postSpyScalperEnable)}
              className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              Enable scalper
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => run("disable", postSpyScalperDisable)}
              className="rounded bg-rose-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-500 disabled:opacity-50"
            >
              Disable scalper
            </button>
          </div>
        </header>

        {error ? <p className="text-sm text-rose-400">Error: {String(error)}</p> : null}

        <SectionCard title="Runtime status">
          <pre className="overflow-x-auto text-xs text-slate-200">
            {JSON.stringify(data?.status ?? {}, null, 2)}
          </pre>
        </SectionCard>

        <SectionCard title="Effective config (defaults + overrides)">
          <pre className="overflow-x-auto text-xs text-slate-200">
            {JSON.stringify(data?.config ?? {}, null, 2)}
          </pre>
        </SectionCard>

        <SectionCard title="Daily summary / metrics">
          <pre className="overflow-x-auto text-xs text-slate-200">
            {JSON.stringify(data?.summary ?? {}, null, 2)}
          </pre>
          <pre className="mt-2 overflow-x-auto text-xs text-slate-300">
            {JSON.stringify(data?.metrics ?? {}, null, 2)}
          </pre>
        </SectionCard>

        <SectionCard title="Recent candidate log">
          <div className="max-h-80 overflow-y-auto text-xs">
            {(data?.signals ?? []).slice(0, 40).map((s) => (
              <div key={s.id} className="border-b border-slate-800 py-1 font-mono text-slate-300">
                {s.created_at} — {s.outcome} — {s.setup_family ?? "-"} — {s.reason ?? ""}
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
