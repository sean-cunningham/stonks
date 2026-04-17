import type { ReactNode } from "react";
import { SectionCard } from "@/components/SectionCard";
import type { StrategyDashboardBundleRead } from "@/types/api";

export type DashboardShellProps = {
  title: string;
  subtitle: string;
  bundle: StrategyDashboardBundleRead | null;
  error: Error | null;
  busy: string | null;
  showPaperReset: boolean;
  apiBase: string;
  pollSeconds: number;
  onEnable: () => void;
  onDisable: () => void;
  onRefresh: () => void;
  onPaperReset?: () => void;
  children?: ReactNode;
};

function rowLabel(r: Record<string, unknown>): string {
  return String(r.outcome ?? r.bucket ?? r.status ?? r.id ?? "");
}

export function DashboardShell({
  title,
  subtitle,
  bundle,
  error,
  busy,
  showPaperReset,
  apiBase,
  pollSeconds,
  onEnable,
  onDisable,
  onRefresh,
  onPaperReset,
  children,
}: DashboardShellProps) {
  const st = bundle?.status;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/80 px-4 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">{title}</h1>
            <p className="text-sm text-slate-400">
              {subtitle} — auto refresh {pollSeconds}s
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!!busy}
              onClick={onEnable}
              className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              Enable
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={onDisable}
              className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
            >
              Disable
            </button>
            {showPaperReset && onPaperReset ? (
              <button
                type="button"
                disabled={!!busy}
                onClick={onPaperReset}
                className="rounded bg-rose-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-600 disabled:opacity-50"
              >
                Paper reset (all strategies)
              </button>
            ) : null}
            <button
              type="button"
              disabled={!!busy}
              onClick={onRefresh}
              className="rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-4 p-4">
        {error && (
          <div className="rounded border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-200">
            API error: {error.message}. Is the backend running on {apiBase}?
          </div>
        )}

        {!bundle && !error && <p className="text-slate-400">Loading…</p>}

        {bundle && st && (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <SectionCard title="Bot state">
                <p className="text-2xl font-semibold capitalize text-white">{st.state}</p>
                {st.pause_reason ? <p className="mt-1 text-sm text-amber-200">{st.pause_reason}</p> : null}
                {st.cooldown_until ? (
                  <p className="mt-1 text-xs text-slate-500">Cooldown until {st.cooldown_until}</p>
                ) : null}
              </SectionCard>
              <SectionCard title="Mode">
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-400">APP_MODE</dt>
                    <dd className="font-mono text-white">{st.app_mode}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Paper-only</dt>
                    <dd className="font-mono text-white">{st.paper_only ? "yes" : "no"}</dd>
                  </div>
                </dl>
              </SectionCard>
              <SectionCard title="Daily P&amp;L snapshot">
                <pre className="overflow-x-auto text-xs text-slate-200">
                  {JSON.stringify(bundle.daily, null, 2)}
                </pre>
              </SectionCard>
            </div>

            {bundle.balances ? (
              <SectionCard title="Balances">
                <pre className="overflow-x-auto text-xs text-slate-200">
                  {JSON.stringify(bundle.balances, null, 2)}
                </pre>
              </SectionCard>
            ) : null}

            <SectionCard title="Open position">
              {bundle.open_position ? (
                <pre className="overflow-x-auto text-xs text-slate-200">
                  {JSON.stringify(bundle.open_position, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-slate-500">No open position for this strategy.</p>
              )}
            </SectionCard>

            <div className="grid gap-4 lg:grid-cols-2">
              <SectionCard title="Recent signals">
                {bundle.signals.length === 0 ? (
                  <p className="text-sm text-slate-500">None.</p>
                ) : (
                  <ul className="max-h-56 space-y-1 overflow-y-auto font-mono text-xs text-slate-300">
                    {bundle.signals.slice(0, 40).map((r, i) => (
                      <li key={String(r.id ?? i)} className="border-b border-slate-800 py-1">
                        <span className="text-slate-500">{String(r.created_at ?? "")}</span>{" "}
                        <span className="text-sky-300">{rowLabel(r)}</span>{" "}
                        <span className="text-slate-400">{String(r.reason ?? r.symbol ?? "")}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
              <SectionCard title="Skipped / rejected setups">
                {bundle.skipped.length === 0 ? (
                  <p className="text-sm text-slate-500">None.</p>
                ) : (
                  <ul className="max-h-56 space-y-1 overflow-y-auto font-mono text-xs text-slate-300">
                    {bundle.skipped.slice(0, 40).map((r, i) => (
                      <li key={String(r.id ?? i)} className="border-b border-slate-800 py-1">
                        <span className="text-slate-500">{String(r.created_at ?? "")}</span>{" "}
                        <span className="text-rose-300">{rowLabel(r)}</span>{" "}
                        <span className="text-slate-400">{String(r.reason ?? r.detail ?? "")}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            <SectionCard title="Recent trades">
              {bundle.trades.length === 0 ? (
                <p className="text-sm text-slate-500">None.</p>
              ) : (
                <ul className="max-h-48 space-y-1 overflow-y-auto font-mono text-xs text-slate-300">
                  {bundle.trades.slice(0, 30).map((r, i) => (
                    <li key={String(r.id ?? i)} className="border-b border-slate-800 py-1">
                      {JSON.stringify(r)}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Metrics">
              <pre className="max-h-64 overflow-auto text-xs text-slate-200">
                {JSON.stringify(bundle.metrics, null, 2)}
              </pre>
            </SectionCard>

            <SectionCard title="Logs / decisions">
              {bundle.logs.length === 0 ? (
                <p className="text-sm text-slate-500">None.</p>
              ) : (
                <ul className="max-h-48 space-y-1 overflow-y-auto font-mono text-xs text-slate-300">
                  {bundle.logs.slice(0, 40).map((r, i) => (
                    <li key={String(r.id ?? i)} className="border-b border-slate-800 py-1">
                      {JSON.stringify(r)}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Config">
              <pre className="max-h-64 overflow-auto text-xs text-slate-200">
                {JSON.stringify(bundle.config, null, 2)}
              </pre>
            </SectionCard>

            {children}
          </>
        )}
      </main>
    </div>
  );
}
