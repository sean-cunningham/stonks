"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cash_balance", sa.Float(), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bot_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("pause_reason", sa.String(length=512), nullable=True),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("underlying_price", sa.Float(), nullable=True),
        sa.Column("bid", sa.Float(), nullable=True),
        sa.Column("ask", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("spread_bps", sa.Float(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_snapshots_symbol", "market_snapshots", ["symbol"])
    op.create_index("ix_market_snapshots_created_at", "market_snapshots", ["created_at"])
    op.create_table(
        "event_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("normalized_event_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("materiality_score", sa.Integer(), nullable=False),
        sa.Column("surprise_score", sa.Integer(), nullable=False),
        sa.Column("direction_bias", sa.String(length=32), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("time_horizon", sa.String(length=32), nullable=False),
        sa.Column("priced_in_risk", sa.String(length=32), nullable=False),
        sa.Column("narrative_summary", sa.Text(), nullable=False),
        sa.Column("key_evidence_points", sa.JSON(), nullable=False),
        sa.Column("tradeability_flag", sa.Boolean(), nullable=False),
        sa.Column("recommended_strategy", sa.String(length=32), nullable=False),
        sa.Column("raw_response_json", sa.Text(), nullable=True),
        sa.Column("validation_ok", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_analyses_created_at", "event_analyses", ["created_at"])
    op.create_index("ix_event_analyses_symbol", "event_analyses", ["symbol"])
    op.create_table(
        "candidate_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("candidate_kind", sa.String(length=64), nullable=False),
        sa.Column("direction_bias", sa.String(length=32), nullable=False),
        sa.Column("legs", sa.JSON(), nullable=False),
        sa.Column("is_event_driven", sa.Boolean(), nullable=False),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_analysis_id"],
            ["event_analyses.id"],
        ),
        sa.ForeignKeyConstraint(
            ["market_snapshot_id"],
            ["market_snapshots.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_trades_created_at", "candidate_trades", ["created_at"])
    op.create_index("ix_candidate_trades_symbol", "candidate_trades", ["symbol"])
    op.create_table(
        "approved_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("candidate_trade_id", sa.Integer(), nullable=False),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_snapshot", sa.JSON(), nullable=True),
        sa.Column("policy_trace", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["candidate_trade_id"],
            ["candidate_trades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_analysis_id"],
            ["event_analyses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approved_trades_created_at", "approved_trades", ["created_at"])
    op.create_table(
        "rejected_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("candidate_trade_id", sa.Integer(), nullable=True),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("rule_codes", sa.JSON(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["candidate_trade_id"],
            ["candidate_trades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_analysis_id"],
            ["event_analyses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rejected_trades_created_at", "rejected_trades", ["created_at"])
    op.create_table(
        "active_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("approved_trade_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("legs", sa.JSON(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("average_entry_price", sa.Float(), nullable=False),
        sa.Column("market_value", sa.Float(), nullable=True),
        sa.Column("unrealized_pnl", sa.Float(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["approved_trade_id"],
            ["approved_trades.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_active_positions_symbol", "active_positions", ["symbol"])
    op.create_index("ix_active_positions_status", "active_positions", ["status"])
    op.create_table(
        "fills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active_position_id", sa.Integer(), nullable=False),
        sa.Column("approved_trade_id", sa.Integer(), nullable=True),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False),
        sa.Column("slip_bps", sa.Float(), nullable=False),
        sa.Column("is_partial", sa.Boolean(), nullable=False),
        sa.Column("leg_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["active_position_id"],
            ["active_positions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["approved_trade_id"],
            ["approved_trades.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fills_created_at", "fills", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_fills_created_at", table_name="fills")
    op.drop_table("fills")
    op.drop_index("ix_active_positions_status", table_name="active_positions")
    op.drop_index("ix_active_positions_symbol", table_name="active_positions")
    op.drop_table("active_positions")
    op.drop_index("ix_rejected_trades_created_at", table_name="rejected_trades")
    op.drop_table("rejected_trades")
    op.drop_index("ix_approved_trades_created_at", table_name="approved_trades")
    op.drop_table("approved_trades")
    op.drop_index("ix_candidate_trades_symbol", table_name="candidate_trades")
    op.drop_index("ix_candidate_trades_created_at", table_name="candidate_trades")
    op.drop_table("candidate_trades")
    op.drop_index("ix_event_analyses_symbol", table_name="event_analyses")
    op.drop_index("ix_event_analyses_created_at", table_name="event_analyses")
    op.drop_table("event_analyses")
    op.drop_index("ix_market_snapshots_created_at", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_symbol", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_table("bot_states")
    op.drop_table("accounts")
