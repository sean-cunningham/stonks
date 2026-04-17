import { useCallback, useState } from "react";
import {
  getTradeReview,
  postPaperReset,
  postStrategyDisable,
  postStrategyEnable,
} from "@/api/client";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { EventEdgeLegacyPanels } from "@/components/dashboard/EventEdgeLegacyPanels";
import { useStrategyDashboard } from "@/hooks/useStrategyDashboard";
import { STRATEGY_EVENT_EDGE_V1, STRATEGY_REGISTRY } from "@/strategies/registry";
import type { StrategyId } from "@/strategies/registry";
import type {
  AnalyticsSummaryResponse,
  RecommendationRead,
  SetupSliceResponse,
  StatusResponse,
  TradeReviewRead,
} from "@/types/api";

const pollMs = Number(import.meta.env.VITE_REFRESH_INTERVAL_MS) || 5000;
const appName = import.meta.env.VITE_APP_NAME || "Stonks";
const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function UnifiedDashboard({ strategyId }: { strategyId: StrategyId }) {
  const meta = STRATEGY_REGISTRY.find((s) => s.id === strategyId)!;
  const { data, error, refresh } = useStrategyDashboard(strategyId, pollMs);
  const [busy, setBusy] = useState<string | null>(null);
  const [reviewTradeId, setReviewTradeId] = useState<number | null>(null);
  const [reviewDetail, setReviewDetail] = useState<TradeReviewRead | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    try {
      await fn();
      refresh();
    } finally {
      setBusy(null);
    }
  }

  const openReview = useCallback(async (approvedTradeId: number) => {
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
  }, []);

  const closeReview = useCallback(() => {
    setReviewTradeId(null);
    setReviewDetail(null);
  }, []);

  const ext = data?.extensions as
    | {
        full_status?: StatusResponse;
        analytics_summary?: AnalyticsSummaryResponse;
        setups?: SetupSliceResponse;
        recommendations?: RecommendationRead[];
      }
    | null
    | undefined;

  const v1Status = ext?.full_status;
  const v1Analytics = ext?.analytics_summary;
  const v1Setups = ext?.setups ?? { setups: [] };
  const v1Recs = ext?.recommendations ?? [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DashboardShell
        title={`${appName} — ${meta.label}`}
        subtitle={meta.description}
        bundle={data}
        error={error}
        busy={busy}
        showPaperReset={strategyId === STRATEGY_EVENT_EDGE_V1}
        apiBase={apiBase}
        pollSeconds={pollMs / 1000}
        onEnable={() => run("enable", () => postStrategyEnable(strategyId))}
        onDisable={() => run("disable", () => postStrategyDisable(strategyId))}
        onRefresh={() => refresh()}
        onPaperReset={
          strategyId === STRATEGY_EVENT_EDGE_V1
            ? () => run("reset", () => postPaperReset())
            : undefined
        }
      >
        {strategyId === STRATEGY_EVENT_EDGE_V1 && v1Status && v1Analytics ? (
          <EventEdgeLegacyPanels
            status={v1Status}
            analyticsSummary={v1Analytics}
            setups={v1Setups}
            recommendations={v1Recs}
            onOpenReview={openReview}
          />
        ) : null}
      </DashboardShell>

      {reviewTradeId != null && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 p-4 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Trade review #{reviewTradeId}</h2>
              <button type="button" className="text-sm text-slate-400 hover:text-white" onClick={closeReview}>
                Close
              </button>
            </div>
            {reviewLoading && <p className="text-sm text-slate-400">Loading…</p>}
            {!reviewLoading && !reviewDetail && (
              <p className="text-sm text-rose-300">No review found yet (trade may still be open or not journaled).</p>
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
                  <span className="text-slate-500">R</span> {reviewDetail.realized_r_multiple?.toFixed(2) ?? "—"}
                </div>
                <div>
                  <span className="text-slate-500">Exit</span> {reviewDetail.exit_quality_label}
                </div>
                <p className="text-xs text-slate-400">{reviewDetail.exit_quality_explanation}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
