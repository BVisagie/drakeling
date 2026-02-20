"""Alembic environment for programmatic migration execution.

This env.py is never invoked via the ``alembic`` CLI.  Instead,
``run_migrations()`` in ``drakeling.storage.database`` passes a live
SQLAlchemy connection through ``config.attributes["connection"]``.
"""
from __future__ import annotations

from alembic import context

from drakeling.storage.models import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = context.config.attributes.get("connection")
    if connectable is None:
        raise RuntimeError("No connection passed via config.attributes")

    context.configure(
        connection=connectable,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
