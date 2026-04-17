"""Live Tastytrade API smoke test (run from backend/: python -m scripts.tastytrade_smoke).

Verifies:
  1. Refresh token -> access token (OAuth)
  2. api-quote-tokens (DXLink / quote streamer credentials)
  3. Option chain nested fetch for an underlying (default SPY)

Requires TASTYTRADE_* credentials in backend/.env (or environment).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.config import Settings
from app.services.market_data.tastytrade_broker import TastytradeBrokerAdapter
from app.services.market_data.token_manager import TokenManager


async def run(symbol: str) -> int:
    settings = Settings()
    tm = TokenManager()
    broker = TastytradeBrokerAdapter(settings, tm)

    await broker.refresh_oauth_if_needed()
    access = tm.get_access_token()
    if not access:
        print("FAIL: no access token after refresh", file=sys.stderr)
        return 1
    print("1 OK refresh_token -> access_token (prefix):", access[:12] + "...")

    dx = await broker.get_dxlink_token()
    print("2 OK api-quote-tokens: token_len=", len(dx["token"]), "dxlink_url=", dx["dxlink_url"])

    chain = await broker.get_option_chain(symbol)
    keys = list(chain.keys()) if isinstance(chain, dict) else []
    print("3 OK", symbol, "option chain top-level keys:", keys[:12])
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Tastytrade API smoke test (live HTTP).")
    p.add_argument(
        "--symbol",
        default="SPY",
        help="Underlying symbol for option chain (default: SPY)",
    )
    args = p.parse_args()
    sym = str(args.symbol or "SPY").strip().upper() or "SPY"
    raise SystemExit(asyncio.run(run(sym)))


if __name__ == "__main__":
    main()
