import type { ReactNode } from "react";
import { SectionCard } from "@/components/SectionCard";
import type { StrategyDashboardBundleRead, StrategyRuntimeHealth } from "@/types/api";

export type DashboardShellProps = {
  title: string;
  subtitle: string;
  bundle: StrategyDashboardBundleRead | null;
  error: Error | null;
  busy: string | null;
  apiBase: string;
  pollSeconds: number;
  onEnable: () => void;
  onDisable: () => void;
  onRefresh: () => void;
  headerActions?: ReactNode;
  children?: ReactNode;
};

function rowLabel(r: Record<string, unknown>): string {
  return String(r.outcome ?? r.bucket ?? r.status ?? r.id ?? "");
}

function parseRuntimeHealth(ext: Record<string, unknown> | null | undefined): StrategyRuntimeHealth | null {
  if (!ext || typeof ext !== "object") return null;
  const raw = ext.runtime_health;
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.safe_to_trade !== "boolean") return null;
  return {
    safe_to_trade: o.safe_to_trade,
    block_reason: typeof o.block_reason === "string" || o.block_reason === null ? (o.block_reason as string | null) : null,
    last_spy_quote_age_sec: typeof o.last_spy_quote_age_sec === "number" ? o.last_spy_quote_age_sec : null,
    last_chain_snapshot_status: String(o.last_chain_snapshot_status ?? ""),
  };
}

function DebugJson({ label, value }: { label: string; value: unknown }) {
  return (
    <details className="group rounded border border-slate-800 bg-slate-950/40">
      <summary className="cursor-pointer select-none px-2 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200">
        {label}
      </summary>
      <pre className="max-h-64 overflow-auto border-t border-slate-800 p-2 text-xs text-slate-200">
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}

export function DashboardShell({
  title,
  subtitle,
  bundle,
  error,
  busy,
  apiBase,
  pollSeconds,
  onEnable,
  onDisable,
  onRefresh,
  headerActions,
  children,
}: DashboardShellProps) {
  const st = bundle?.status;
  const ext = bundle?.extensions as Record<string, unknown> | null | undefined;
  const runtimeHealth = parseRuntimeHealth(ext);

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
            {headerActions}
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
            {runtimeHealth ? (
              <SectionCard title="Runtime">
                <dl className="grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
                  <div className="flex justify-between gap-2 border-b border-slate-800 pb-1 sm:block sm:border-0 sm:pb-0">
                    <dt className="text-slate-400">APP_MODE</dt>
                    <dd className="font-mono text-white">{st.app_mode}</dd>
                  </div>
                  <div className="flex justify-between gap-2 border-b border-slate-800 pb-1 sm:block sm:border-0 sm:pb-0">
                    <dt className="text-slate-400">Paper-only</dt>
                    <dd className="font-mono text-white">{st.paper_only ? "yes" : "no"}</dd>
                  </div>
                  <div className="flex justify-between gap-2 border-b border-slate-800 pb-1 sm:block sm:border-0 sm:pb-0">
                    <dt className="text-slate-400">Safe to trade</dt>
                    <dd className={`font-mono ${runtimeHealth.safe_to_trade ? "text-emerald-300" : "text-amber-300"}`}>
                      {runtimeHealth.safe_to_trade ? "yes" : "no"}
                    </dd>
                  </div>
                  <div className="sm:col-span-2 lg:col-span-1">
                    <dt className="text-slate-400">Block reason</dt>
                    <dd className="font-mono text-xs text-slate-200">{runtimeHealth.block_reason ?? "—"}</dd>
                  </div>
                  <div className="flex justify-between gap-2 sm:block">
                    <dt className="text-slate-400">SPY quote age (s)</dt>
                    <dd className="font-mono text-white">
                      {runtimeHealth.last_spy_quote_age_sec != null ? runtimeHealth.last_spy_quote_age_sec.toFixed(1) : "—"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-2 sm:block">
                    <dt className="text-slate-400">Chain snapshot</dt>
                    <dd className="font-mono text-white">{runtimeHealth.last_chain_snapshot_status}</dd>
                  </div>
                </dl>
              </SectionCard>
            ) : null}

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
                <DebugJson label="Debug JSON — daily" value={bundle.daily} />
              </SectionCard>
            </div>

            {bundle.balances ? (
              <SectionCard title="Balances">
                <DebugJson label="Debug JSON — balances" value={bundle.balances} />
              </SectionCard>
            ) : null}

            <SectionCard title="Open position">
              {bundle.open_position ? (
                <DebugJson label="Debug JSON — open position" value={bundle.open_position} />
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
                <ul className="max-h-48 space-y-2 overflow-y-auto font-mono text-xs text-slate-300">
                  {bundle.trades.slice(0, 30).map((r, i) => (
                    <li key={String(r.id ?? i)} className="border-b border-slate-800 py-1">
                      <DebugJson label={`Trade #${String(r.id ?? i)}`} value={r} />
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Metrics">
              <DebugJson label="Debug JSON — metrics" value={bundle.metrics} />
            </SectionCard>

            <SectionCard title="Logs / decisions">
              {bundle.logs.length === 0 ? (
                <p className="text-sm text-slate-500">None.</p>
              ) : (
                <ul className="max-h-48 space-y-2 overflow-y-auto font-mono text-xs text-slate-300">
                  {bundle.logs.slice(0, 40).map((r, i) => (
                    <li key={String((r as Record<string, unknown>).id ?? i)} className="border-b border-slate-800 py-1">
                      <DebugJson label={`Log #${i}`} value={r} />
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Config">
              <DebugJson label="Debug JSON — config" value={bundle.config} />
            </SectionCard>

            {children}
          </>
        )}
      </main>
    </div>
  );
}
