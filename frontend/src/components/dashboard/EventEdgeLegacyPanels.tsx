import { PnlChart } from "@/components/PnlChart";
import { SectionCard } from "@/components/SectionCard";
import type {
  AnalyticsSummaryResponse,
  ApprovedTradeRead,
  CandidateTradeRead,
  DecisionSnapshotRead,
  EventAnalysisRead,
  FillRead,
  RejectedTradeRead,
  RecommendationRead,
  SetupSliceResponse,
  StatusResponse,
} from "@/types/api";

export type EventEdgeLegacyPanelsProps = {
  status: StatusResponse;
  analyticsSummary: AnalyticsSummaryResponse;
  setups: SetupSliceResponse;
  recommendations: RecommendationRead[];
  onOpenReview: (approvedTradeId: number) => void;
};

export function EventEdgeLegacyPanels({
  status,
  analyticsSummary,
  setups,
  recommendations,
  onOpenReview,
}: EventEdgeLegacyPanelsProps) {
  const ac = status.analytics_compact;
  const setupRows = setups.setups ?? [];

  return (
    <div className="space-y-4">
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
              <div className="font-mono text-lg text-white">{(ac.overall_win_rate * 100).toFixed(1)}%</div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/50 p-2">
              <div className="text-slate-500">Expectancy / trade</div>
              <div className="font-mono text-lg text-white">{ac.overall_expectancy_usd.toFixed(2)} USD</div>
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

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard title="Top reason codes (closed trades)">
          {analyticsSummary.top_reason_codes.length === 0 ? (
            <p className="text-sm text-slate-500">No reason-code snapshots yet.</p>
          ) : (
            <ul className="space-y-1 text-sm text-slate-300">
              {analyticsSummary.top_reason_codes.map((rc) => (
                <li key={rc.reason_code} className="flex justify-between border-b border-slate-800/80 py-1">
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
              {Object.entries(analyticsSummary.anticipatory_vs_confirmed).map(([family, m]) => (
                <li key={family} className="rounded border border-slate-800 bg-slate-950/40 p-2">
                  <div className="font-medium text-white">{family}</div>
                  <div className="font-mono text-xs text-slate-400">
                    n={(m.trade_count as number) ?? 0} · win{" "}
                    {((((m.win_rate as number) ?? 0) * 100).toFixed(1))}% · E{" "}
                    {((m.expectancy as number) ?? 0).toFixed(2)} USD
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Setup performance & expectancy">
        {setupRows.length === 0 ? (
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
                {setupRows.map((row) => (
                  <tr key={String(row.setup_type)} className="border-t border-slate-800">
                    <td className="py-1 text-sky-200">{String(row.setup_type)}</td>
                    <td>{String(row.trade_count)}</td>
                    <td>{(((row.win_rate as number) ?? 0) * 100).toFixed(0)}</td>
                    <td>{((row.expectancy as number) ?? 0).toFixed(2)}</td>
                    <td>{row.avg_realized_r != null ? (row.avg_realized_r as number).toFixed(2) : "—"}</td>
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
              <li key={r.id} className="rounded border border-amber-900/30 bg-amber-950/10 p-2">
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
        <ActivePositionsPanel positions={status.active_positions} />
        <CandidatesPanel candidates={status.recent_candidates} />
        <RejectionsPanel rejections={status.recent_rejections} />
        <EventAnalysesPanel analyses={status.recent_event_analyses} />
        <FillsPanel fills={status.recent_fills} />
        <ApprovedTradesPanel trades={status.recent_trades} onOpenReview={onOpenReview} />
        <DecisionsPanel decisions={status.recent_decisions} />
      </div>

      <p className="text-center text-xs text-slate-600">
        Snapshot: {status.latest_account_snapshot_at ?? "—"}
      </p>
    </div>
  );
}

function ActivePositionsPanel({ positions }: { positions: StatusResponse["active_positions"] }) {
  return (
    <SectionCard title="Active positions">
      {positions.length === 0 ? (
        <p className="text-sm text-slate-500">No open positions.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {positions.map((p) => (
            <li key={p.id} className="rounded border border-slate-800 bg-slate-950/60 p-2">
              <span className="font-medium text-white">{p.symbol}</span>{" "}
              <span className="text-slate-400">{p.strategy}</span>
              <div className="mt-1 font-mono text-xs text-slate-400">
                qty {p.quantity} @ {p.average_entry_price.toFixed(3)} · uPnL {(p.unrealized_pnl ?? 0).toFixed(2)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function CandidatesPanel({ candidates }: { candidates: CandidateTradeRead[] }) {
  return (
    <SectionCard title="Recent candidates">
      {candidates.length === 0 ? (
        <p className="text-sm text-slate-500">No candidates yet.</p>
      ) : (
        <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
          {candidates.map((c) => (
            <li key={c.id} className="rounded border border-slate-800 bg-slate-950/60 p-2">
              <span className="text-white">{c.symbol}</span> <span className="text-slate-400">{c.strategy}</span>
              <div className="text-xs text-slate-500">{c.candidate_kind}</div>
              <div className="text-xs text-sky-300">
                setup {c.setup_type ?? "—"} · score {(c.setup_score ?? 0).toFixed(1)} ·{" "}
                {c.confirmation_state ?? "unknown"}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function RejectionsPanel({ rejections }: { rejections: RejectedTradeRead[] }) {
  return (
    <SectionCard title="Rejections">
      {rejections.length === 0 ? (
        <p className="text-sm text-slate-500">No rejections logged.</p>
      ) : (
        <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
          {rejections.map((r) => (
            <li key={r.id} className="rounded border border-rose-900/40 bg-rose-950/20 p-2">
              <div className="text-rose-200">{r.reasons.join(" · ")}</div>
              <div className="text-xs text-slate-500">{r.rule_codes.join(", ")}</div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function EventAnalysesPanel({ analyses }: { analyses: EventAnalysisRead[] }) {
  return (
    <SectionCard title="AI event analyses">
      {analyses.length === 0 ? (
        <p className="text-sm text-slate-500">No analyses yet.</p>
      ) : (
        <ul className="max-h-48 space-y-2 overflow-y-auto text-sm">
          {analyses.map((e) => (
            <li key={e.id} className="rounded border border-slate-800 bg-slate-950/60 p-2">
              <div className="font-medium text-white">
                {e.symbol} · {e.event_type} · {e.event_source_tier}
              </div>
              <div className="text-slate-300">{e.narrative_summary}</div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function FillsPanel({ fills }: { fills: FillRead[] }) {
  return (
    <SectionCard title="Recent fills">
      {fills.length === 0 ? (
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
            {fills.map((f) => (
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
  );
}

function ApprovedTradesPanel({
  trades,
  onOpenReview,
}: {
  trades: ApprovedTradeRead[];
  onOpenReview: (id: number) => void;
}) {
  return (
    <SectionCard title="Recent approved trades">
      {trades.length === 0 ? (
        <p className="text-sm text-slate-500">No approved trades.</p>
      ) : (
        <ul className="text-sm text-slate-300">
          {trades.map((t) => (
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
                  onClick={() => onOpenReview(t.id)}
                >
                  Trade review
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function DecisionsPanel({ decisions }: { decisions: DecisionSnapshotRead[] }) {
  return (
    <SectionCard title="Decision buckets">
      {decisions.length === 0 ? (
        <p className="text-sm text-slate-500">No decisions yet.</p>
      ) : (
        <ul className="max-h-56 space-y-2 overflow-y-auto text-xs">
          {decisions.map((d) => (
            <li key={d.id} className="rounded border border-slate-800 bg-slate-950/60 p-2">
              <div className="text-slate-200">
                {d.symbol} · <span className="text-sky-300">{d.bucket}</span> · {d.strategy_track}
              </div>
              <div className="text-slate-500">
                {(d.weighted_score ?? 0).toFixed(2)} · {(d.hard_veto_codes || []).join(", ")}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
