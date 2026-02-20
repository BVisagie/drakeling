from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drakeling.storage.models import Base

DB_FILENAME = "drakeling.db"


def get_engine(data_dir: Path):
    db_path = data_dir / DB_FILENAME
    return create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)


def get_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(engine) -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
