import type {
  AnalyticsSummaryResponse,
  BotStateRead,
  DashboardBundle,
  RecommendationRead,
  SetupSliceResponse,
  SpyScalperSignalRead,
  SpyScalperStatusRead,
  StatusResponse,
  TradeReviewRead,
} from "@/types/api";

const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${base}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${t}`);
  }
  return r.json() as Promise<T>;
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

export function getSpyScalperStatus(): Promise<SpyScalperStatusRead> {
  return fetchJson<SpyScalperStatusRead>("/strategies/spy-0dte-scalper/status");
}

export function postSpyScalperEnable(): Promise<SpyScalperStatusRead> {
  return fetchJson<SpyScalperStatusRead>("/strategies/spy-0dte-scalper/enable", { method: "POST" });
}

export function postSpyScalperDisable(): Promise<SpyScalperStatusRead> {
  return fetchJson<SpyScalperStatusRead>("/strategies/spy-0dte-scalper/disable", { method: "POST" });
}

export function getSpyScalperConfig(): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>("/strategies/spy-0dte-scalper/config");
}

export function getSpyScalperMetricsDaily(): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>("/strategies/spy-0dte-scalper/metrics/daily");
}

export function getSpyScalperSignalsRecent(): Promise<SpyScalperSignalRead[]> {
  return fetchJson<SpyScalperSignalRead[]>("/strategies/spy-0dte-scalper/signals/recent");
}

export function getSpyScalperSummaryDaily(): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>("/strategies/spy-0dte-scalper/summary/daily");
}
