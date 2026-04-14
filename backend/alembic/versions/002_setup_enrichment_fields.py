"""add setup, enrichment, and trade-management fields

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("event_analyses", sa.Column("event_source_tier", sa.String(length=32), nullable=False, server_default="official"))
    op.add_column("event_analyses", sa.Column("escalation_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("event_analyses", sa.Column("setup_score", sa.Float(), nullable=True))
    op.add_column("event_analyses", sa.Column("reason_codes", sa.JSON(), nullable=True))

    op.add_column("candidate_trades", sa.Column("setup_type", sa.String(length=64), nullable=True))
    op.add_column("candidate_trades", sa.Column("setup_score", sa.Float(), nullable=True))
    op.add_column("candidate_trades", sa.Column("reason_codes", sa.JSON(), nullable=True))
    op.add_column("candidate_trades", sa.Column("confirmation_state", sa.String(length=32), nullable=True))
    op.add_column("candidate_trades", sa.Column("event_id", sa.String(length=128), nullable=True))
    op.create_index("ix_candidate_trades_setup_type", "candidate_trades", ["setup_type"])

    op.add_column("active_positions", sa.Column("initial_stop_price", sa.Float(), nullable=True))
    op.add_column("active_positions", sa.Column("emergency_premium_stop_pct", sa.Float(), nullable=True))
    op.add_column("active_positions", sa.Column("current_trailing_stop", sa.Float(), nullable=True))
    op.add_column("active_positions", sa.Column("breakeven_armed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("active_positions", sa.Column("partial_exit_taken", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("active_positions", sa.Column("partial_exit_qty", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("active_positions", sa.Column("thesis_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "x_enrichments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("candidate_trade_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("sentiment_bias", sa.String(length=32), nullable=False),
        sa.Column("acceleration_flag", sa.Boolean(), nullable=False),
        sa.Column("rumor_risk_flag", sa.Boolean(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_points", sa.JSON(), nullable=False),
        sa.Column("raw_response_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_trade_id"], ["candidate_trades.id"]),
        sa.ForeignKeyConstraint(["event_analysis_id"], ["event_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_x_enrichments_created_at", "x_enrichments", ["created_at"])
    op.create_index("ix_x_enrichments_symbol", "x_enrichments", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_x_enrichments_symbol", table_name="x_enrichments")
    op.drop_index("ix_x_enrichments_created_at", table_name="x_enrichments")
    op.drop_table("x_enrichments")

    op.drop_column("active_positions", "thesis_expires_at")
    op.drop_column("active_positions", "partial_exit_qty")
    op.drop_column("active_positions", "partial_exit_taken")
    op.drop_column("active_positions", "breakeven_armed")
    op.drop_column("active_positions", "current_trailing_stop")
    op.drop_column("active_positions", "emergency_premium_stop_pct")
    op.drop_column("active_positions", "initial_stop_price")

    op.drop_index("ix_candidate_trades_setup_type", table_name="candidate_trades")
    op.drop_column("candidate_trades", "event_id")
    op.drop_column("candidate_trades", "confirmation_state")
    op.drop_column("candidate_trades", "reason_codes")
    op.drop_column("candidate_trades", "setup_score")
    op.drop_column("candidate_trades", "setup_type")

    op.drop_column("event_analyses", "reason_codes")
    op.drop_column("event_analyses", "setup_score")
    op.drop_column("event_analyses", "escalation_used")
    op.drop_column("event_analyses", "event_source_tier")
