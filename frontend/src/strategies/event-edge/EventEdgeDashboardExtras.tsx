import { useCallback, useState } from "react";
import { getTradeReview, postStrategyPaperReset } from "@/api/client";
import { EventEdgeLegacyPanels } from "@/strategies/event-edge/EventEdgeLegacyPanels";
import { STRATEGY_EVENT_EDGE_V1 } from "@/strategies/registry";
import type {
  AnalyticsSummaryResponse,
  RecommendationRead,
  SetupSliceResponse,
  StatusResponse,
  StrategyDashboardBundleRead,
  TradeReviewRead,
} from "@/types/api";

type EventEdgeDashboardExtrasProps = {
  strategyId: string;
  bundle: StrategyDashboardBundleRead | null;
};

type EventEdgeHeaderActionsProps = {
  busy: string | null;
  run: (label: string, fn: () => Promise<unknown>) => Promise<void>;
};

export function EventEdgeHeaderActions({ busy, run }: EventEdgeHeaderActionsProps) {
  return (
    <button
      type="button"
      disabled={!!busy}
      onClick={() => run("reset", () => postStrategyPaperReset(STRATEGY_EVENT_EDGE_V1))}
      className="rounded bg-rose-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-600 disabled:opacity-50"
    >
      Paper reset (Event Edge only)
    </button>
  );
}

export function EventEdgeDashboardExtras({ strategyId, bundle }: EventEdgeDashboardExtrasProps) {
  const [reviewTradeId, setReviewTradeId] = useState<number | null>(null);
  const [reviewDetail, setReviewDetail] = useState<TradeReviewRead | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  const ext = bundle?.extensions as
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

  if (strategyId !== STRATEGY_EVENT_EDGE_V1) {
    return null;
  }

  return (
    <>
      {v1Status && v1Analytics ? (
        <EventEdgeLegacyPanels
          status={v1Status}
          analyticsSummary={v1Analytics}
          setups={v1Setups}
          recommendations={v1Recs}
          onOpenReview={openReview}
        />
      ) : null}

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
    </>
  );
}
