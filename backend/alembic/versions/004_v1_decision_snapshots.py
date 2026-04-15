"""add deterministic decision snapshots

Revision ID: 004
Revises: 003
Create Date: 2026-04-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decision_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("candidate_trade_id", sa.Integer(), nullable=True),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("approved_trade_id", sa.Integer(), nullable=True),
        sa.Column("bucket", sa.String(length=32), nullable=False),
        sa.Column("strategy_track", sa.String(length=32), nullable=False),
        sa.Column("hard_vetoes", sa.JSON(), nullable=False),
        sa.Column("hard_veto_codes", sa.JSON(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("weighted_score", sa.Float(), nullable=True),
        sa.Column("market_state_json", sa.JSON(), nullable=False),
        sa.Column("option_state_json", sa.JSON(), nullable=False),
        sa.Column("risk_state_json", sa.JSON(), nullable=False),
        sa.Column("context_state_json", sa.JSON(), nullable=False),
        sa.Column("historical_state_json", sa.JSON(), nullable=False),
        sa.Column("order_instruction_json", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_trade_id"], ["approved_trades.id"]),
        sa.ForeignKeyConstraint(["candidate_trade_id"], ["candidate_trades.id"]),
        sa.ForeignKeyConstraint(["event_analysis_id"], ["event_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_snapshots_created_at", "decision_snapshots", ["created_at"])
    op.create_index("ix_decision_snapshots_symbol", "decision_snapshots", ["symbol"])
    op.create_index("ix_decision_snapshots_bucket", "decision_snapshots", ["bucket"])
    op.create_index("ix_decision_snapshots_strategy_track", "decision_snapshots", ["strategy_track"])


def downgrade() -> None:
    op.drop_index("ix_decision_snapshots_strategy_track", table_name="decision_snapshots")
    op.drop_index("ix_decision_snapshots_bucket", table_name="decision_snapshots")
    op.drop_index("ix_decision_snapshots_symbol", table_name="decision_snapshots")
    op.drop_index("ix_decision_snapshots_created_at", table_name="decision_snapshots")
    op.drop_table("decision_snapshots")
