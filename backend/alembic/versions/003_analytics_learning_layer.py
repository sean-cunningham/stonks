"""analytics learning layer: trade reviews, snapshots, recommendations, experiments

Revision ID: 003
Revises: 002
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("active_positions", sa.Column("high_water_mark_price", sa.Float(), nullable=True))
    op.add_column("active_positions", sa.Column("low_water_mark_price", sa.Float(), nullable=True))
    op.add_column(
        "active_positions",
        sa.Column("reached_1r", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "active_positions",
        sa.Column("reached_1_5r", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "active_positions",
        sa.Column("reached_2r", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "trade_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_trade_id", sa.Integer(), nullable=False),
        sa.Column("candidate_trade_id", sa.Integer(), nullable=True),
        sa.Column("active_position_id", sa.Integer(), nullable=True),
        sa.Column("event_analysis_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("setup_type", sa.String(length=64), nullable=True),
        sa.Column("setup_score", sa.Float(), nullable=True),
        sa.Column("confirmation_state", sa.String(length=32), nullable=True),
        sa.Column("event_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=True),
        sa.Column("trade_family", sa.String(length=32), nullable=False, server_default="confirmed"),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("exit_reason", sa.String(length=64), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("realized_pnl_dollars", sa.Float(), nullable=False),
        sa.Column("realized_r_multiple", sa.Float(), nullable=True),
        sa.Column("mfe_dollars", sa.Float(), nullable=True),
        sa.Column("mae_dollars", sa.Float(), nullable=True),
        sa.Column("holding_seconds", sa.Integer(), nullable=True),
        sa.Column("hit_plus_1r", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hit_plus_1_5r", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hit_plus_2r", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rule_adherence_ok", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("had_x_enrichment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("had_thenewsapi_supplement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason_codes_snapshot", sa.JSON(), nullable=True),
        sa.Column("policy_trace_snapshot", sa.JSON(), nullable=True),
        sa.Column("exit_quality_label", sa.String(length=64), nullable=True),
        sa.Column("exit_quality_explanation", sa.Text(), nullable=True),
        sa.Column("journaling_version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["active_position_id"], ["active_positions.id"]),
        sa.ForeignKeyConstraint(["approved_trade_id"], ["approved_trades.id"]),
        sa.ForeignKeyConstraint(["candidate_trade_id"], ["candidate_trades.id"]),
        sa.ForeignKeyConstraint(["event_analysis_id"], ["event_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approved_trade_id", name="uq_trade_reviews_approved_trade_id"),
    )
    op.create_index("ix_trade_reviews_created_at", "trade_reviews", ["created_at"])
    op.create_index("ix_trade_reviews_approved_trade_id", "trade_reviews", ["approved_trade_id"])
    op.create_index("ix_trade_reviews_symbol", "trade_reviews", ["symbol"])
    op.create_index("ix_trade_reviews_setup_type", "trade_reviews", ["setup_type"])
    op.create_index("ix_trade_reviews_trade_family", "trade_reviews", ["trade_family"])

    op.create_table(
        "setup_performance_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dimension_type", sa.String(length=32), nullable=False),
        sa.Column("dimension_key", sa.String(length=128), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("trade_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_setup_performance_snapshots_computed_at", "setup_performance_snapshots", ["computed_at"])
    op.create_index("ix_setup_performance_snapshots_dimension_type", "setup_performance_snapshots", ["dimension_type"])
    op.create_index("ix_setup_performance_snapshots_dimension_key", "setup_performance_snapshots", ["dimension_key"])

    op.create_table(
        "recommendation_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("affected_scope", sa.JSON(), nullable=False),
        sa.Column("suggested_parameter_delta", sa.JSON(), nullable=True),
        sa.Column("trade_review_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["trade_review_id"], ["trade_reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendation_items_created_at", "recommendation_items", ["created_at"])
    op.create_index("ix_recommendation_items_status", "recommendation_items", ["status"])

    op.create_table(
        "parameter_experiment_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trade_review_id", sa.Integer(), nullable=False),
        sa.Column("experiment_name", sa.String(length=128), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("outcome_summary", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["trade_review_id"], ["trade_reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parameter_experiment_results_created_at", "parameter_experiment_results", ["created_at"])
    op.create_index("ix_parameter_experiment_results_trade_review_id", "parameter_experiment_results", ["trade_review_id"])
    op.create_index("ix_parameter_experiment_results_experiment_name", "parameter_experiment_results", ["experiment_name"])


def downgrade() -> None:
    op.drop_index("ix_parameter_experiment_results_experiment_name", table_name="parameter_experiment_results")
    op.drop_index("ix_parameter_experiment_results_trade_review_id", table_name="parameter_experiment_results")
    op.drop_index("ix_parameter_experiment_results_created_at", table_name="parameter_experiment_results")
    op.drop_table("parameter_experiment_results")

    op.drop_index("ix_recommendation_items_status", table_name="recommendation_items")
    op.drop_index("ix_recommendation_items_created_at", table_name="recommendation_items")
    op.drop_table("recommendation_items")

    op.drop_index("ix_setup_performance_snapshots_dimension_key", table_name="setup_performance_snapshots")
    op.drop_index("ix_setup_performance_snapshots_dimension_type", table_name="setup_performance_snapshots")
    op.drop_index("ix_setup_performance_snapshots_computed_at", table_name="setup_performance_snapshots")
    op.drop_table("setup_performance_snapshots")

    op.drop_index("ix_trade_reviews_trade_family", table_name="trade_reviews")
    op.drop_index("ix_trade_reviews_setup_type", table_name="trade_reviews")
    op.drop_index("ix_trade_reviews_symbol", table_name="trade_reviews")
    op.drop_index("ix_trade_reviews_approved_trade_id", table_name="trade_reviews")
    op.drop_index("ix_trade_reviews_created_at", table_name="trade_reviews")
    op.drop_table("trade_reviews")

    op.drop_column("active_positions", "reached_2r")
    op.drop_column("active_positions", "reached_1_5r")
    op.drop_column("active_positions", "reached_1r")
    op.drop_column("active_positions", "low_water_mark_price")
    op.drop_column("active_positions", "high_water_mark_price")
