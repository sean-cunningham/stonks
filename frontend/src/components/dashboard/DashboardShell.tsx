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

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number" && Number.isFinite(v)) return String(v);
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
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
    app_mode: typeof o.app_mode === "string" ? o.app_mode : undefined,
    api_degraded: typeof o.api_degraded === "boolean" ? o.api_degraded : o.api_degraded === null ? null : undefined,
    chain_snapshot_age_sec: typeof o.chain_snapshot_age_sec === "number" ? o.chain_snapshot_age_sec : null,
    last_quote_tick_iso: typeof o.last_quote_tick_iso === "string" ? o.last_quote_tick_iso : null,
    live_candidate_pipeline_enabled: typeof o.live_candidate_pipeline_enabled === "boolean" ? o.live_candidate_pipeline_enabled : undefined,
    spy_scalper_synthetic_blocked:
      typeof o.spy_scalper_synthetic_blocked === "boolean" ? o.spy_scalper_synthetic_blocked : null,
    spy_scalper_synthetic_block_reason:
      typeof o.spy_scalper_synthetic_block_reason === "string" || o.spy_scalper_synthetic_block_reason === null
        ? (o.spy_scalper_synthetic_block_reason as string | null)
        : null,
  };
}

function KeyValueTable({ rows }: { rows: { k: string; v: string }[] }) {
  if (rows.length === 0) return <p className="text-sm text-slate-500">No rows.</p>;
  return (
    <table className="w-full text-left text-sm">
      <tbody>
        {rows.map((r) => (
          <tr key={r.k} className="border-b border-slate-800">
            <td className="py-1.5 pr-4 align-top text-slate-400">{r.k}</td>
            <td className="py-1.5 font-mono text-xs text-slate-100">{r.v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function objectToRows(obj: Record<string, unknown>, max = 24): { k: string; v: string }[] {
  return Object.entries(obj)
    .slice(0, max)
    .map(([k, v]) => ({ k, v: fmt(v) }));
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
  const rh = parseRuntimeHealth(ext);

  const s1Pipeline =
    st?.live_candidate_pipeline_enabled ?? rh?.live_candidate_pipeline_enabled ?? null;
  const spySynth =
    st?.spy_scalper_synthetic_blocked ?? rh?.spy_scalper_synthetic_blocked ?? null;
  const spySynthReason = st?.spy_scalper_synthetic_block_reason ?? rh?.spy_scalper_synthetic_block_reason ?? null;

  const liveMockLabel =
    rh?.app_mode === "mock"
      ? "mock"
      : rh?.api_degraded === true
        ? "degraded"
        : rh?.api_degraded === false
          ? "live"
          : st?.app_mode === "mock"
            ? "mock"
            : "live / unknown";

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
            <SectionCard title="Runtime and connectivity">
              <div className="grid gap-4 lg:grid-cols-2">
                <KeyValueTable
                  rows={[
                    { k: "Bot state", v: st.state },
                    { k: "APP_MODE (status)", v: st.app_mode },
                    { k: "APP_MODE (health)", v: rh?.app_mode ?? "—" },
                    { k: "Live / mock / degraded", v: liveMockLabel },
                    { k: "Paper-only", v: st.paper_only ? "yes" : "no" },
                    {
                      k: "Safe to trade",
                      v: rh ? (rh.safe_to_trade ? "yes" : "no") : "—",
                    },
                    { k: "Block reason", v: rh?.block_reason ?? "—" },
                    {
                      k: "SPY quote age (s)",
                      v: rh?.last_spy_quote_age_sec != null ? rh.last_spy_quote_age_sec.toFixed(2) : "—",
                    },
                    { k: "Chain snapshot status", v: rh?.last_chain_snapshot_status ?? "—" },
                    {
                      k: "Chain snapshot age (s)",
                      v: rh?.chain_snapshot_age_sec != null ? rh.chain_snapshot_age_sec.toFixed(1) : "—",
                    },
                    {
                      k: "API degraded (snapshot)",
                      v: rh?.api_degraded === true ? "yes" : rh?.api_degraded === false ? "no" : "—",
                    },
                    { k: "Last quote tick (ISO)", v: rh?.last_quote_tick_iso ?? "—" },
                  ]}
                />
                <KeyValueTable
                  rows={[
                    {
                      k: "Strategy 1 live candidate pipeline",
                      v: s1Pipeline === null ? "—" : s1Pipeline ? "on" : "off",
                    },
                    {
                      k: "Strategy 2 synthetic path",
                      v: spySynth === null ? "n/a" : spySynth ? "blocked (non-mock)" : "allowed (mock)",
                    },
                    { k: "Strategy 2 block detail", v: spySynthReason ?? "—" },
                  ]}
                />
              </div>
            </SectionCard>

            <div className="grid gap-4 md:grid-cols-2">
              <SectionCard title="Bot state">
                <p className="text-2xl font-semibold capitalize text-white">{st.state}</p>
                {st.pause_reason ? <p className="mt-1 text-sm text-amber-200">{st.pause_reason}</p> : null}
                {st.cooldown_until ? (
                  <p className="mt-1 text-xs text-slate-500">Cooldown until {st.cooldown_until}</p>
                ) : null}
              </SectionCard>
              <SectionCard title="Daily summary">
                <KeyValueTable rows={objectToRows(bundle.daily as Record<string, unknown>)} />
              </SectionCard>
            </div>

            {bundle.balances ? (
              <SectionCard title="Balances">
                <KeyValueTable rows={objectToRows(bundle.balances as Record<string, unknown>)} />
              </SectionCard>
            ) : null}

            <SectionCard title="Open position">
              {bundle.open_position ? (
                <KeyValueTable rows={objectToRows(bundle.open_position as Record<string, unknown>)} />
              ) : (
                <p className="text-sm text-slate-500">No open position for this strategy.</p>
              )}
            </SectionCard>

            <div className="grid gap-4 lg:grid-cols-2">
              <SectionCard title="Recent signals">
                {bundle.signals.length === 0 ? (
                  <p className="text-sm text-slate-500">None.</p>
                ) : (
                  <div className="max-h-56 overflow-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="sticky top-0 bg-slate-900 text-slate-400">
                        <tr>
                          <th className="py-1 pr-2">Time</th>
                          <th className="py-1 pr-2">Outcome</th>
                          <th className="py-1">Note</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bundle.signals.slice(0, 40).map((r, i) => {
                          const row = r as Record<string, unknown>;
                          return (
                            <tr key={String(row.id ?? i)} className="border-b border-slate-800">
                              <td className="py-1 pr-2 font-mono text-slate-500">{String(row.created_at ?? "")}</td>
                              <td className="py-1 pr-2 text-sky-300">{rowLabel(row)}</td>
                              <td className="py-1 text-slate-400">{String(row.reason ?? row.symbol ?? "")}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </SectionCard>
              <SectionCard title="Skipped / rejected setups">
                {bundle.skipped.length === 0 ? (
                  <p className="text-sm text-slate-500">None.</p>
                ) : (
                  <div className="max-h-56 overflow-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="sticky top-0 bg-slate-900 text-slate-400">
                        <tr>
                          <th className="py-1 pr-2">Time</th>
                          <th className="py-1 pr-2">Outcome</th>
                          <th className="py-1">Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bundle.skipped.slice(0, 40).map((r, i) => {
                          const row = r as Record<string, unknown>;
                          return (
                            <tr key={String(row.id ?? i)} className="border-b border-slate-800">
                              <td className="py-1 pr-2 font-mono text-slate-500">{String(row.created_at ?? "")}</td>
                              <td className="py-1 pr-2 text-rose-300">{rowLabel(row)}</td>
                              <td className="py-1 text-slate-400">{String(row.reason ?? row.detail ?? "")}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </SectionCard>
            </div>

            <SectionCard title="Recent trades">
              {bundle.trades.length === 0 ? (
                <p className="text-sm text-slate-500">None.</p>
              ) : (
                <div className="max-h-64 overflow-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="sticky top-0 bg-slate-900 text-slate-400">
                      <tr>
                        <th className="py-1 pr-2">Id</th>
                        <th className="py-1 pr-2">Opened</th>
                        <th className="py-1 pr-2">Closed</th>
                        <th className="py-1 pr-2">Family</th>
                        <th className="py-1 pr-2">P&amp;L</th>
                        <th className="py-1">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bundle.trades.slice(0, 30).map((r, i) => {
                        const row = r as Record<string, unknown>;
                        return (
                          <tr key={String(row.id ?? i)} className="border-b border-slate-800">
                            <td className="py-1 pr-2 font-mono">{String(row.id ?? "")}</td>
                            <td className="py-1 pr-2 font-mono text-slate-500">{String(row.opened_at ?? "")}</td>
                            <td className="py-1 pr-2 font-mono text-slate-500">{String(row.closed_at ?? "")}</td>
                            <td className="py-1 pr-2">{String(row.setup_family ?? "")}</td>
                            <td className="py-1 pr-2">{fmt(row.realized_pnl)}</td>
                            <td className="py-1">{String(row.close_reason ?? "")}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            <SectionCard title="Metrics">
              <KeyValueTable rows={objectToRows(bundle.metrics as Record<string, unknown>, 40)} />
            </SectionCard>

            <SectionCard title="Logs / decisions">
              {bundle.logs.length === 0 ? (
                <p className="text-sm text-slate-500">None.</p>
              ) : (
                <div className="max-h-64 overflow-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="sticky top-0 bg-slate-900 text-slate-400">
                      <tr>
                        <th className="py-1 pr-2">Id</th>
                        <th className="py-1 pr-2">Time</th>
                        <th className="py-1 pr-2">Bucket / outcome</th>
                        <th className="py-1 pr-2">Symbol</th>
                        <th className="py-1">Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bundle.logs.slice(0, 40).map((r, i) => {
                        const row = r as Record<string, unknown>;
                        const summary = String(row.explanation ?? row.reason ?? "").slice(0, 200);
                        return (
                          <tr key={String(row.id ?? i)} className="border-b border-slate-800">
                            <td className="py-1 pr-2 font-mono">{String(row.id ?? "")}</td>
                            <td className="py-1 pr-2 font-mono text-slate-500">{String(row.created_at ?? "")}</td>
                            <td className="py-1 pr-2">{String(row.bucket ?? row.outcome ?? "")}</td>
                            <td className="py-1 pr-2">{String(row.symbol ?? "")}</td>
                            <td className="py-1 text-slate-400">{summary}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            <SectionCard title="Config">
              <p className="mb-2 text-xs text-slate-500">
                Read-only: {bundle.config.read_only ? "yes" : "no"}
              </p>
              <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">Effective</h3>
              <KeyValueTable rows={objectToRows((bundle.config.effective ?? {}) as Record<string, unknown>, 40)} />
            </SectionCard>

            {children}
          </>
        )}
      </main>
    </div>
  );
}
