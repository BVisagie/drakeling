from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CreatureStateRow(Base):
    __tablename__ = "creature_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    colour: Mapped[str] = mapped_column(String(10), nullable=False)
    personality_seed: Mapped[str] = mapped_column(String(64), nullable=False)

    # Permanent traits (fixed at birth)
    trait_curiosity: Mapped[float] = mapped_column(Float, nullable=False)
    trait_sociability: Mapped[float] = mapped_column(Float, nullable=False)
    trait_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    trait_emotional_sensitivity: Mapped[float] = mapped_column(Float, nullable=False)
    trait_autonomy_preference: Mapped[float] = mapped_column(Float, nullable=False)
    trait_loneliness_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # Mutable state
    mood: Mapped[float] = mapped_column(Float, nullable=False)
    energy: Mapped[float] = mapped_column(Float, nullable=False)
    trust: Mapped[float] = mapped_column(Float, nullable=False)
    trust_floor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    loneliness: Mapped[float] = mapped_column(Float, nullable=False)
    state_curiosity: Mapped[float] = mapped_column(Float, nullable=False)
    stability: Mapped[float] = mapped_column(Float, nullable=False)

    # Lifecycle
    lifecycle_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    pre_exhausted_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pre_resting_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timestamps
    born_at: Mapped[float] = mapped_column(Float, nullable=False)
    hatched_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Identity
    public_key_hex: Mapped[str] = mapped_column(Text, nullable=False)

    # Cumulative counters
    cumulative_care_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cumulative_talk_interactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Reflection tracking
    last_reflection_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Bookkeeping
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)


class CreatureMemoryRow(Base):
    __tablename__ = "creature_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(20), nullable=False)


class InteractionLogRow(Base):
    __tablename__ = "interaction_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    care_type: Mapped[str | None] = mapped_column(String(20), nullable=True)


class LifecycleEventRow(Base):
    __tablename__ = "lifecycle_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
