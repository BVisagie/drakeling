from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DB_FILENAME = "drakeling.db"

_MIGRATIONS_DIR = str(Path(__file__).parent / "migrations")


def get_engine(data_dir: Path):
    db_path = data_dir / DB_FILENAME
    return create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)


def get_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _run_alembic(connection) -> None:  # type: ignore[no-untyped-def]
    from alembic import command
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", _MIGRATIONS_DIR)
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def run_migrations(engine) -> None:
    """Run Alembic migrations to head."""
    async with engine.begin() as conn:
        await conn.run_sync(_run_alembic)
