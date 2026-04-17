import type { StrategyConfigRead, StrategyDashboardBundleRead, StrategyListItemRead, TradeReviewRead } from "@/types/api";
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

export function postStrategyPaperReset(strategyId: StrategyId): Promise<StrategyDashboardBundleRead["status"]> {
  return fetchJson<StrategyDashboardBundleRead["status"]>(`/strategies/${strategyId}/paper-reset`, {
    method: "POST",
  });
}

export function putStrategyConfig(
  strategyId: StrategyId,
  overrides: Record<string, unknown>,
): Promise<StrategyConfigRead> {
  return fetchJson<StrategyConfigRead>(`/strategies/${strategyId}/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overrides }),
  });
}

export function getTradeReview(approvedTradeId: number): Promise<TradeReviewRead> {
  return fetchJson<TradeReviewRead>(`/analytics/trades/${approvedTradeId}/review`);
}
