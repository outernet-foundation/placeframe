from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

if os.environ.get("CODEGEN"):

    async def get_session() -> AsyncGenerator[AsyncSession]:
        yield AsyncSession()

else:
    settings = get_settings()

    SessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_orchestration_user}:{settings.database_orchestration_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
            pool_pre_ping=True,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def get_session() -> AsyncGenerator[AsyncSession]:
        async with SessionLocal() as session, session.begin():
            yield session
