import { useCallback, useState } from "react";
import {
  getDashboardBundle,
  postBotStart,
  postBotStop,
  postPaperReset,
  getTradeReview,
} from "@/api/client";
import { PnlChart } from "@/components/PnlChart";
import { SectionCard } from "@/components/SectionCard";
import { usePolling } from "@/hooks/usePolling";
import type { TradeReviewRead } from "@/types/api";

const appName = import.meta.env.VITE_APP_NAME || "Stonks";
const pollMs = Number(import.meta.env.VITE_REFRESH_INTERVAL_MS) || 5000;

export function Dashboard() {
  const fetchAll = useCallback(() => getDashboardBundle(), []);
  const { data, error, refresh } = usePolling(fetchAll, pollMs);
  const [busy, setBusy] = useState<string | null>(null);
  const [reviewTradeId, setReviewTradeId] = useState<number | null>(null);
  const [reviewDetail, setReviewDetail] = useState<TradeReviewRead | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  async function run(
    label: string,
    fn: () => Promise<unknown>,
  ): Promise<void> {
    setBusy(label);
    try {
      await fn();
      refresh();
    } finally {
      setBusy(null);
    }
  }

  async function openReview(approvedTradeId: number) {
    setReviewTradeId(approvedTradeId);
    setReviewLoading(true);
    setReviewDetail(null);
    try {
      const r = await getTradeReview(approvedTradeId);
      setReviewDetail(r);
    } catch {
      setReviewDetail(null);
    } finally {
      setReviewLoading(false);
    }
  }

  function closeReview() {
    setReviewTradeId(null);
    setReviewDetail(null);
  }

  const status = data?.status;
  const analyticsSummary = data?.analyticsSummary;
  const setups = data?.setups?.setups ?? [];
  const recommendations = data?.recommendations ?? [];
  const ac = status?.analytics_compact;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/80 px-4 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">{appName}</h1>
            <p className="text-sm text-slate-400">
              Paper trading dashboard — auto refresh {pollMs / 1000}s
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!!busy}
              onClick={() => run("start", postBotStart)}
              className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              Start bot
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => run("stop", postBotStop)}
              className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
            >
              Stop bot
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => run("reset", postPaperReset)}
              className="rounded bg-rose-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-600 disabled:opacity-50"
            >
              Paper reset
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-4 p-4">
        {error && (
          <div className="rounded border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-200">
            API error: {error.message}. Is the backend running on{" "}
            {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}?
          </div>
        )}

        {!data && !error && (
          <p className="text-slate-400">Loading status…</p>
        )}

        {status && (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <SectionCard title="Bot">
                <p className="text-2xl font-semibold capitalize text-white">
                  {status.bot.state}
                </p>
                {status.bot.pause_reason && (
                  <p className="mt-1 text-sm text-amber-200">
                    {status.bot.pause_reason}
                  </p>
                )}
              </SectionCard>
              <SectionCard title="Balances">
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Cash</dt>
                    <dd className="font-mono text-white">
                      {status.balances.cash.toFixed(2)} {status.balances.currency}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">In trades</dt>
                    <dd className="font-mono text-white">
                      {status.balances.in_trades.toFixed(2)}
                    </dd>
                  </div>
                  <div className="flex justify-between border-t border-slate-800 pt-2">
                    <dt className="text-slate-300">Total equity</dt>
                    <dd className="font-mono font-semibold text-sky-300">
                      {status.balances.total.toFixed(2)}
                    </dd>
                  </div>
                </dl>
              </SectionCard>
              <SectionCard title="P&L">
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Realized</dt>
                    <dd
                      className={
                        status.realized_pnl >= 0
                          ? "font-mono text-emerald-400"
                          : "font-mono text-rose-400"
                      }
                    >
                      {status.realized_pnl.toFixed(2)}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Unrealized</dt>
                    <dd className="font-mono text-slate-200">
                      {status.unrealized_pnl.toFixed(2)}
                    </dd>
                  </div>
                </dl>
              </SectionCard>
            </div>

            {ac && (
              <SectionCard title="Learning analytics (read-only)">
                <p className="mb-3 text-xs text-amber-200/90">{ac.governance_note}</p>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
                  <div className="rounded border border-slate-800 bg-slate-950/50 p-2">
                    <div className="text-slate-500">Completed trade reviews</div>
                    <div className="font-mono text-lg text-white">{ac.trade_review_count}</div>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-950/50 p-2">
                    <div className="text-slate-500">Win rate (sample)</div>
                    <div className="font-mono text-lg text-white">
                      {(ac.overall_win_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-950/50 p-2">
                    <div className="text-slate-500">Expectancy / trade</div>
                    <div className="font-mono text-lg text-white">
                      {ac.overall_expectancy_usd.toFixed(2)} USD
                    </div>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-950/50 p-2">
                    <div className="text-slate-500">Avg realized R</div>
                    <div className="font-mono text-lg text-white">
                      {ac.avg_realized_r != null ? ac.avg_realized_r.toFixed(2) : "—"}
                    </div>
                  </div>
                </div>
                {ac.setup_expectancy_preview.length > 0 && (
                  <div className="mt-3 text-xs text-slate-400">
                    <span className="text-slate-500">Setup preview: </span>
                    {ac.setup_expectancy_preview.map((s) => (
                      <span key={s.setup_type} className="mr-3 inline-block">
                        {s.setup_type} ({s.n}): {s.expectancy.toFixed(2)} USD
                      </span>
                    ))}
                  </div>
                )}
              </SectionCard>
            )}

            {analyticsSummary && (
              <div className="grid gap-4 lg:grid-cols-3">
                <SectionCard title="Top reason codes (closed trades)">
                  {analyticsSummary.top_reason_codes.length === 0 ? (
                    <p className="text-sm text-slate-500">No reason-code snapshots yet.</p>
                  ) : (
                    <ul className="space-y-1 text-sm text-slate-300">
                      {analyticsSummary.top_reason_codes.map((rc) => (
                        <li
                          key={rc.reason_code}
                          className="flex justify-between border-b border-slate-800/80 py-1"
                        >
                          <span className="text-slate-400">{rc.reason_code}</span>
                          <span className="font-mono">{rc.count}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>
                <SectionCard title="Exit quality summary">
                  {Object.keys(analyticsSummary.exit_quality).length === 0 ? (
                    <p className="text-sm text-slate-500">No closed-trade reviews yet.</p>
                  ) : (
                    <ul className="space-y-1 text-sm text-slate-300">
                      {Object.entries(analyticsSummary.exit_quality)
                        .sort((a, b) => b[1] - a[1])
                        .map(([k, v]) => (
                          <li key={k} className="flex justify-between border-b border-slate-800/80 py-1">
                            <span>{k}</span>
                            <span className="font-mono text-slate-400">{v}</span>
                          </li>
                        ))}
                    </ul>
                  )}
                </SectionCard>
                <SectionCard title="Anticipatory vs confirmed">
                  {Object.keys(analyticsSummary.anticipatory_vs_confirmed).length === 0 ? (
                    <p className="text-sm text-slate-500">No slices yet.</p>
                  ) : (
                    <ul className="space-y-2 text-sm text-slate-300">
                      {Object.entries(analyticsSummary.anticipatory_vs_confirmed).map(
                        ([family, m]) => (
                          <li
                            key={family}
                            className="rounded border border-slate-800 bg-slate-950/40 p-2"
                          >
                            <div className="font-medium text-white">{family}</div>
                            <div className="font-mono text-xs text-slate-400">
                              n={(m.trade_count as number) ?? 0} · win{" "}
                              {((((m.win_rate as number) ?? 0) * 100).toFixed(1))}% · E{" "}
                              {((m.expectancy as number) ?? 0).toFixed(2)} USD
                            </div>
                          </li>
                        ),
                      )}
                    </ul>
                  )}
                </SectionCard>
              </div>
            )}

            <SectionCard title="Setup performance & expectancy">
              {setups.length === 0 ? (
                <p className="text-sm text-slate-500">No per-setup stats yet.</p>
              ) : (
                <div className="max-h-56 overflow-y-auto text-sm">
                  <table className="w-full text-left text-xs">
                    <thead className="sticky top-0 bg-slate-900 text-slate-500">
                      <tr>
                        <th className="pb-2">Setup</th>
                        <th>n</th>
                        <th>Win%</th>
                        <th>E $</th>
                        <th>Avg R</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono text-slate-200">
                      {setups.map((row) => (
                        <tr key={String(row.setup_type)} className="border-t border-slate-800">
                          <td className="py-1 text-sky-200">{String(row.setup_type)}</td>
                          <td>{String(row.trade_count)}</td>
                          <td>{(((row.win_rate as number) ?? 0) * 100).toFixed(0)}</td>
                          <td>{((row.expectancy as number) ?? 0).toFixed(2)}</td>
                          <td>
                            {row.avg_realized_r != null
                              ? (row.avg_realized_r as number).toFixed(2)
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            <SectionCard title="Suggested changes for review (not auto-applied)">
              <p className="mb-2 text-xs text-amber-200/80">
                Recommendations are for human review only. They do not change live rules or execution.
              </p>
              {recommendations.length === 0 ? (
                <p className="text-sm text-slate-500">No recommendations stored.</p>
              ) : (
                <ul className="max-h-64 space-y-2 overflow-y-auto text-sm">
                  {recommendations.map((r) => (
                    <li
                      key={r.id}
                      className="rounded border border-amber-900/30 bg-amber-950/10 p-2"
                    >
                      <div className="font-medium text-amber-100">{r.title}</div>
                      <div className="text-xs text-slate-400">{r.evidence_summary}</div>
                      <div className="mt-1 text-xs text-slate-500">
                        confidence {(r.confidence * 100).toFixed(0)}% · {r.status}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="P&L chart">
              <PnlChart
                realized={status.realized_pnl}
                unrealized={status.unrealized_pnl}
                fillsCount={status.recent_fills.length}
              />
            </SectionCard>

            <div className="grid gap-4 lg:grid-cols-2">
              <SectionCard title="Active positions">
                {status.active_positions.length === 0 ? (
                  <p className="text-sm text-slate-500">No open positions.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {status.active_positions.map((p) => (
                      <li
                        key={p.id}
                        className="rounded border border-slate-800 bg-slate-950/60 p-2"
                      >
                        <span className="font-medium text-white">{p.symbol}</span>{" "}
                        <span className="text-slate-400">{p.strategy}</span>
                        <div className="mt-1 font-mono text-xs text-slate-400">
                          qty {p.quantity} @ {p.average_entry_price.toFixed(3)} · uPnL{" "}
                          {(p.unrealized_pnl ?? 0).toFixed(2)}
                        </div>
                        <div className="mt-1 text-xs text-slate-500">
                          stop {p.current_trailing_stop?.toFixed(3) ?? "—"} · breakeven{" "}
                          {p.breakeven_armed ? "armed" : "no"} · partial{" "}
                          {p.partial_exit_taken ? `yes (${p.partial_exit_qty})` : "no"}
                        </div>
                        <div className="mt-1 text-xs text-slate-600">
                          MFE/MAE marks {p.high_water_mark_price?.toFixed(3) ?? "—"} /{" "}
                          {p.low_water_mark_price?.toFixed(3) ?? "—"} · R hits{" "}
                          {[p.reached_1r && "1R", p.reached_1_5r && "1.5R", p.reached_2r && "2R"]
                            .filter(Boolean)
                            .join(", ") || "—"}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <SectionCard title="Recent candidates">
                {status.recent_candidates.length === 0 ? (
                  <p className="text-sm text-slate-500">No candidates yet.</p>
                ) : (
                  <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
                    {status.recent_candidates.map((c) => (
                      <li
                        key={c.id}
                        className="rounded border border-slate-800 bg-slate-950/60 p-2"
                      >
                        <span className="text-white">{c.symbol}</span>{" "}
                        <span className="text-slate-400">{c.strategy}</span>
                        <div className="text-xs text-slate-500">{c.candidate_kind}</div>
                        <div className="text-xs text-sky-300">
                          setup {c.setup_type ?? "—"} · score{" "}
                          {(c.setup_score ?? 0).toFixed(1)} · {c.confirmation_state ?? "unknown"}
                        </div>
                        {c.reason_codes && c.reason_codes.length > 0 && (
                          <div className="text-xs text-slate-500">{c.reason_codes.join(", ")}</div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <SectionCard title="Rejections">
                {status.recent_rejections.length === 0 ? (
                  <p className="text-sm text-slate-500">No rejections logged.</p>
                ) : (
                  <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
                    {status.recent_rejections.map((r) => (
                      <li
                        key={r.id}
                        className="rounded border border-rose-900/40 bg-rose-950/20 p-2"
                      >
                        <div className="text-rose-200">{r.reasons.join(" · ")}</div>
                        <div className="text-xs text-slate-500">
                          {r.rule_codes.join(", ")}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <SectionCard title="AI event analyses">
                {status.recent_event_analyses.length === 0 ? (
                  <p className="text-sm text-slate-500">No analyses yet.</p>
                ) : (
                  <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
                    {status.recent_event_analyses.map((e) => (
                      <li
                        key={e.id}
                        className="rounded border border-slate-800 bg-slate-950/60 p-2"
                      >
                        <div className="font-medium text-white">
                          {e.symbol} · {e.event_type} · {e.event_source_tier}
                        </div>
                        <div className="text-slate-300">{e.narrative_summary}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          bias {e.direction_bias} · tradeable{" "}
                          {e.tradeability_flag ? "yes" : "no"}
                        </div>
                        <div className="text-xs text-slate-500">
                          setupScore {(e.setup_score ?? 0).toFixed(1)} · escalation{" "}
                          {e.escalation_used ? "yes" : "no"}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <SectionCard title="Optional x-enrichment (secondary)">
                {status.recent_x_enrichments.length === 0 ? (
                  <p className="text-sm text-slate-500">No sidecar enrichments.</p>
                ) : (
                  <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
                    {status.recent_x_enrichments.map((x) => (
                      <li
                        key={x.id}
                        className="rounded border border-indigo-900/40 bg-indigo-950/20 p-2"
                      >
                        <div className="text-indigo-200">
                          {x.symbol} · {x.model_name} · sentiment {x.sentiment_bias}
                        </div>
                        <div className="text-xs text-slate-400">{x.summary}</div>
                        <div className="text-xs text-slate-500">
                          acceleration {x.acceleration_flag ? "yes" : "no"} · rumor risk{" "}
                          {x.rumor_risk_flag ? "high" : "low"}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <SectionCard title="Recent fills">
                {status.recent_fills.length === 0 ? (
                  <p className="text-sm text-slate-500">No fills.</p>
                ) : (
                  <table className="w-full text-left text-xs">
                    <thead className="text-slate-500">
                      <tr>
                        <th className="pb-2">Side</th>
                        <th>Qty</th>
                        <th>Price</th>
                        <th>Partial</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono text-slate-200">
                      {status.recent_fills.map((f) => (
                        <tr key={f.id} className="border-t border-slate-800">
                          <td className="py-1">{f.side}</td>
                          <td>{f.quantity}</td>
                          <td>{f.price.toFixed(3)}</td>
                          <td>{f.is_partial ? "yes" : "no"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </SectionCard>

              <SectionCard title="Recent approved trades">
                {status.recent_trades.length === 0 ? (
                  <p className="text-sm text-slate-500">No approved trades.</p>
                ) : (
                  <ul className="text-sm text-slate-300">
                    {status.recent_trades.map((t) => (
                      <li
                        key={t.id}
                        className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 py-1"
                      >
                        <span>
                          #{t.id} · {t.status} · {t.created_at}
                        </span>
                        {t.status === "filled" && (
                          <button
                            type="button"
                            className="rounded bg-slate-800 px-2 py-0.5 text-xs text-sky-300 hover:bg-slate-700"
                            onClick={() => openReview(t.id)}
                          >
                            Trade review
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            <p className="text-center text-xs text-slate-600">
              Snapshot: {status.latest_account_snapshot_at ?? "—"}
            </p>
          </>
        )}
      </main>

      {reviewTradeId != null && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 p-4 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                Trade review #{reviewTradeId}
              </h2>
              <button
                type="button"
                className="text-sm text-slate-400 hover:text-white"
                onClick={closeReview}
              >
                Close
              </button>
            </div>
            {reviewLoading && <p className="text-sm text-slate-400">Loading…</p>}
            {!reviewLoading && !reviewDetail && (
              <p className="text-sm text-rose-300">
                No review found yet (trade may still be open or not journaled).
              </p>
            )}
            {reviewDetail && (
              <div className="space-y-2 text-sm text-slate-300">
                <div>
                  <span className="text-slate-500">Symbol</span> {reviewDetail.symbol}
                </div>
                <div>
                  <span className="text-slate-500">P&amp;L</span>{" "}
                  <span className="font-mono">{reviewDetail.realized_pnl_dollars.toFixed(2)} USD</span>
                </div>
                <div>
                  <span className="text-slate-500">R</span>{" "}
                  {reviewDetail.realized_r_multiple?.toFixed(2) ?? "—"}
                </div>
                <div>
                  <span className="text-slate-500">MFE / MAE</span>{" "}
                  {reviewDetail.mfe_dollars?.toFixed(2) ?? "—"} /{" "}
                  {reviewDetail.mae_dollars?.toFixed(2) ?? "—"}
                </div>
                <div>
                  <span className="text-slate-500">Exit</span> {reviewDetail.exit_quality_label}
                </div>
                <p className="text-xs text-slate-400">{reviewDetail.exit_quality_explanation}</p>
                <div className="text-xs text-slate-500">
                  enrichment {reviewDetail.had_x_enrichment ? "yes" : "no"} · TheNewsAPI{" "}
                  {reviewDetail.had_thenewsapi_supplement ? "yes" : "no"}
                </div>
                {reviewDetail.shadow_experiments.length > 0 && (
                  <div className="mt-3 border-t border-slate-800 pt-2">
                    <div className="text-slate-500">Shadow experiments</div>
                    <ul className="mt-1 space-y-2">
                      {reviewDetail.shadow_experiments.map((ex) => (
                        <li key={ex.id} className="rounded bg-slate-950/80 p-2 text-xs">
                          <div className="font-medium text-slate-200">{ex.experiment_name}</div>
                          <div className="text-slate-400">{ex.outcome_summary}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
