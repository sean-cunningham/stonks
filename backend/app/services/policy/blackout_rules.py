from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class BlackoutConfig:
    minutes_before_close: int = 30
    tz: str = "America/New_York"


def in_no_new_trades_window(now: datetime, cfg: BlackoutConfig) -> bool:
    """US equities: block new trades in last N minutes before 16:00 ET (simplified, no holidays)."""
    et = now.astimezone(ZoneInfo(cfg.tz))
    if et.weekday() >= 5:
        return True
    close_h, close_m = 16, 0
    close_today = et.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    delta_min = (close_today - et).total_seconds() / 60
    return 0 <= delta_min <= cfg.minutes_before_close
