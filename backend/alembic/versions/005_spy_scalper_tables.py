"""spy 0dte scalper strategy tables and strategy_bot_states

Revision ID: 005
Revises: 004
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategy_bot_states",
        sa.Column("strategy_slug", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="stopped"),
        sa.Column("pause_reason", sa.String(length=512), nullable=True),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("scalper_state_json", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("strategy_slug"),
    )
    op.create_table(
        "spy_scalper_candidate_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trade_day", sa.String(length=16), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("setup_family", sa.String(length=64), nullable=True),
        sa.Column("direction", sa.String(length=8), nullable=True),
        sa.Column("base_score", sa.Float(), nullable=True),
        sa.Column("ai_adjustment", sa.Float(), nullable=True),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("features_json", sa.JSON(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_spy_scalper_candidate_events_trade_day",
        "spy_scalper_candidate_events",
        ["trade_day"],
    )
    op.create_index(
        "ix_spy_scalper_candidate_events_created_at",
        "spy_scalper_candidate_events",
        ["created_at"],
    )
    op.create_table(
        "spy_scalper_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False, server_default="SPY"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("right", sa.String(length=4), nullable=False),
        sa.Column("strike", sa.Float(), nullable=False),
        sa.Column("expiry", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("entry_mid", sa.Float(), nullable=False),
        sa.Column("entry_fill_price", sa.Float(), nullable=False),
        sa.Column("exit_fill_price", sa.Float(), nullable=True),
        sa.Column("current_mark", sa.Float(), nullable=True),
        sa.Column("unrealized_pnl", sa.Float(), nullable=True),
        sa.Column("realized_pnl", sa.Float(), nullable=True),
        sa.Column("setup_family", sa.String(length=64), nullable=True),
        sa.Column("high_water_mark", sa.Float(), nullable=True),
        sa.Column("low_water_mark", sa.Float(), nullable=True),
        sa.Column("take_profit_price", sa.Float(), nullable=True),
        sa.Column("stop_price", sa.Float(), nullable=True),
        sa.Column("max_hold_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fast_fail_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_spy_scalper_positions_status", "spy_scalper_positions", ["status"])
    op.create_table(
        "spy_scalper_fills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["position_id"], ["spy_scalper_positions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_spy_scalper_fills_position_id", "spy_scalper_fills", ["position_id"])
    op.create_table(
        "spy_scalper_daily_summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("summary_date", sa.String(length=16), nullable=False),
        sa.Column("net_pnl", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trades_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("by_family_json", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("summary_date"),
    )


def downgrade() -> None:
    op.drop_table("spy_scalper_daily_summaries")
    op.drop_index("ix_spy_scalper_fills_position_id", table_name="spy_scalper_fills")
    op.drop_table("spy_scalper_fills")
    op.drop_index("ix_spy_scalper_positions_status", table_name="spy_scalper_positions")
    op.drop_table("spy_scalper_positions")
    op.drop_index("ix_spy_scalper_candidate_events_created_at", table_name="spy_scalper_candidate_events")
    op.drop_index("ix_spy_scalper_candidate_events_trade_day", table_name="spy_scalper_candidate_events")
    op.drop_table("spy_scalper_candidate_events")
    op.drop_table("strategy_bot_states")
