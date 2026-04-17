import { useCallback, useEffect, useState } from "react";
import { getStrategyDashboard } from "@/api/client";
import type { StrategyDashboardBundleRead } from "@/types/api";
import type { StrategyId } from "@/strategies/registry";

export function useStrategyDashboard(strategyId: StrategyId, pollMs: number) {
  const fetchBundle = useCallback(async () => {
    return getStrategyDashboard(strategyId);
  }, [strategyId]);

  const [data, setData] = useState<StrategyDashboardBundleRead | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchBundle()
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e : new Error(String(e)));
      });
    return () => {
      cancelled = true;
    };
  }, [fetchBundle, tick]);

  useEffect(() => {
    const id = setInterval(() => setTick((x) => x + 1), pollMs);
    return () => clearInterval(id);
  }, [pollMs]);

  const refresh = useCallback(() => setTick((x) => x + 1), []);

  return { data, error, refresh };
}
