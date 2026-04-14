from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.active_position import ActivePosition
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.rejection_repository import RejectionRepository
from app.repositories.trade_repository import TradeRepository
from app.services.policy.blackout_rules import BlackoutConfig, in_no_new_trades_window
from app.services.policy.fusion_engine import evaluate_fusion
from app.services.risk.limits import RiskLimits
from app.services.risk.risk_engine import check_risk


class ApprovalEngine:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._rej = RejectionRepository(db)
        self._tr = TradeRepository(db)

    def try_approve(self, candidate_id: int) -> tuple[str, int | None]:
        """Returns ('approved', trade_id) or ('rejected', rejection_id)."""
        cand = self._db.get(CandidateTrade, candidate_id)
        if not cand:
            r = self._rej.create(reasons=["candidate not found"], rule_codes=["NOT_FOUND"])
            return "rejected", r.id

        snap: MarketSnapshot | None = None
        if cand.market_snapshot_id:
            snap = self._db.get(MarketSnapshot, cand.market_snapshot_id)

        event_row: EventAnalysis | None = None
        if cand.event_analysis_id:
            event_row = self._db.get(EventAnalysis, cand.event_analysis_id)

        from app.models.account import Account
        from app.models.bot_state import BotStateRow

        account = self._db.get(Account, 1)
        bot = self._db.get(BotStateRow, 1)
        if not account or not bot:
            r = self._rej.create(
                reasons=["missing account or bot state"],
                rule_codes=["STATE"],
                candidate_trade_id=cand.id,
            )
            return "rejected", r.id

        open_rows = list(
            self._db.scalars(
                select(ActivePosition).where(ActivePosition.status == "open"),
            ).all(),
        )

        fusion = evaluate_fusion(
            candidate=cand,
            snapshot=snap,
            event_row=event_row,
            open_positions=open_rows,
        )

        limits = RiskLimits(
            max_risk_per_trade_pct=self._settings.bot_default_max_risk_per_trade_pct,
            max_open_positions=self._settings.bot_default_max_open_positions,
            max_daily_loss_pct=self._settings.bot_default_max_daily_loss_pct,
            max_weekly_loss_pct=self._settings.bot_default_max_weekly_loss_pct,
        )
        risk = check_risk(
            account=account,
            bot=bot,
            open_position_count=len(open_rows),
            limits=limits,
        )
        if "daily_loss_breach" in risk.reasons:
            BotStateRepository(self._db).set_state(
                "paused",
                pause_reason="daily_loss_breach",
            )

        cfg = BlackoutConfig(
            minutes_before_close=self._settings.bot_no_new_trades_minutes_before_close,
        )
        blackout = (
            in_no_new_trades_window(utc_now(), cfg)
            if self._settings.app_mode != AppMode.MOCK
            else False
        )

        all_reasons: list[str] = []
        codes: list[str] = []
        if not fusion.ok:
            all_reasons.extend(fusion.reasons)
            codes.extend(fusion.failed_rules)
        if not risk.ok:
            all_reasons.extend(risk.reasons)
            codes.extend(risk.reasons)
        if blackout:
            all_reasons.append("blackout_near_close")
            codes.append("BLACKOUT")

        if all_reasons:
            r = self._rej.create(
                reasons=all_reasons,
                rule_codes=codes,
                candidate_trade_id=cand.id,
                event_analysis_id=cand.event_analysis_id,
            )
            return "rejected", r.id

        at = self._tr.create_approved(
            candidate_trade_id=cand.id,
            event_analysis_id=cand.event_analysis_id,
            status="pending",
            risk_snapshot={"max_risk_pct": limits.max_risk_per_trade_pct},
            policy_trace={"fusion": "ok", "risk": "ok"},
        )
        return "approved", at.id
