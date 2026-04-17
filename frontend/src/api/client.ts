import type {
  AnalyticsSummaryResponse,
  BotStateRead,
  DashboardBundle,
  RecommendationRead,
  SetupSliceResponse,
  StatusResponse,
  StrategyDashboardBundleRead,
  StrategyListItemRead,
  TradeReviewRead,
} from "@/types/api";
import type { StrategyId } from "@/strategies/registry";

const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${base}${path}`;
  const r = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${t}`);
  }
  return r.json() as Promise<T>;
}

export function getStrategyList(): Promise<StrategyListItemRead[]> {
  return fetchJson<StrategyListItemRead[]>("/strategies");
}

export function getStrategyDashboard(strategyId: StrategyId): Promise<StrategyDashboardBundleRead> {
  return fetchJson<StrategyDashboardBundleRead>(`/strategies/${strategyId}/dashboard`);
}

export function postStrategyEnable(strategyId: StrategyId): Promise<StrategyDashboardBundleRead["status"]> {
  return fetchJson<StrategyDashboardBundleRead["status"]>(`/strategies/${strategyId}/enable`, {
    method: "POST",
  });
}

export function postStrategyDisable(strategyId: StrategyId): Promise<StrategyDashboardBundleRead["status"]> {
  return fetchJson<StrategyDashboardBundleRead["status"]>(`/strategies/${strategyId}/disable`, {
    method: "POST",
  });
}

export function putStrategyConfig(
  strategyId: StrategyId,
  overrides: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>(`/strategies/${strategyId}/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overrides }),
  });
}

export function getStatus(): Promise<StatusResponse> {
  return fetchJson<StatusResponse>("/status");
}

export function getAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  return fetchJson<AnalyticsSummaryResponse>("/analytics/summary");
}

export function getAnalyticsSetups(): Promise<SetupSliceResponse> {
  return fetchJson<SetupSliceResponse>("/analytics/setups");
}

export function getAnalyticsRecommendations(refresh: boolean): Promise<RecommendationRead[]> {
  return fetchJson<RecommendationRead[]>(`/analytics/recommendations?refresh=${refresh}`);
}

export function getTradeReview(approvedTradeId: number): Promise<TradeReviewRead> {
  return fetchJson<TradeReviewRead>(`/analytics/trades/${approvedTradeId}/review`);
}

export async function getDashboardBundle(): Promise<DashboardBundle> {
  const [status, analyticsSummary, setups, recommendations] = await Promise.all([
    getStatus(),
    getAnalyticsSummary(),
    getAnalyticsSetups(),
    getAnalyticsRecommendations(false),
  ]);
  return { status, analyticsSummary, setups, recommendations };
}

export function getBotState(): Promise<BotStateRead> {
  return fetchJson<BotStateRead>("/bot/state");
}

export function postBotStart(): Promise<BotStateRead> {
  return fetchJson<BotStateRead>("/bot/start", { method: "POST" });
}

export function postBotStop(): Promise<BotStateRead> {
  return fetchJson<BotStateRead>("/bot/stop", { method: "POST" });
}

export function postPaperReset(): Promise<BotStateRead> {
  return fetchJson<BotStateRead>("/bot/paper-reset", { method: "POST" });
}
