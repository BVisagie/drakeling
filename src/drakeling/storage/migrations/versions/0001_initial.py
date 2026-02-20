"""Baseline schema.

Revision ID: 0001
Revises: None
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "creature_state",
        sa.Column("id", sa.Integer, primary_key=True, default=1),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("colour", sa.String(10), nullable=False),
        sa.Column("personality_seed", sa.String(64), nullable=False),
        sa.Column("trait_curiosity", sa.Float, nullable=False),
        sa.Column("trait_sociability", sa.Float, nullable=False),
        sa.Column("trait_confidence", sa.Float, nullable=False),
        sa.Column("trait_emotional_sensitivity", sa.Float, nullable=False),
        sa.Column("trait_autonomy_preference", sa.Float, nullable=False),
        sa.Column("trait_loneliness_rate", sa.Float, nullable=False),
        sa.Column("mood", sa.Float, nullable=False),
        sa.Column("energy", sa.Float, nullable=False),
        sa.Column("trust", sa.Float, nullable=False),
        sa.Column("trust_floor", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("loneliness", sa.Float, nullable=False),
        sa.Column("state_curiosity", sa.Float, nullable=False),
        sa.Column("stability", sa.Float, nullable=False),
        sa.Column("lifecycle_stage", sa.String(20), nullable=False),
        sa.Column("pre_exhausted_stage", sa.String(20), nullable=True),
        sa.Column("pre_resting_stage", sa.String(20), nullable=True),
        sa.Column("born_at", sa.Float, nullable=False),
        sa.Column("hatched_at", sa.Float, nullable=True),
        sa.Column("public_key_hex", sa.Text, nullable=False),
        sa.Column("cumulative_care_events", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cumulative_talk_interactions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_reflection_at", sa.Float, nullable=True),
        sa.Column("updated_at", sa.Float, nullable=False),
    )

    op.create_table(
        "creature_memory",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.Float, nullable=False),
        sa.Column("memory_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("lifecycle_stage", sa.String(20), nullable=False),
    )

    op.create_table(
        "interaction_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.Float, nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("interaction_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("care_type", sa.String(20), nullable=True),
    )

    op.create_table(
        "lifecycle_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.Float, nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("from_stage", sa.String(20), nullable=True),
        sa.Column("to_stage", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("lifecycle_events")
    op.drop_table("interaction_log")
    op.drop_table("creature_memory")
    op.drop_table("creature_state")
