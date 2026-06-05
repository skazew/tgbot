"""Налаштування async-двигуна SQLAlchemy і фабрики сесій."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import load_config
from database.models import Base

_config = load_config()

engine: AsyncEngine = create_async_engine(_config.database_url, echo=False, future=True)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
