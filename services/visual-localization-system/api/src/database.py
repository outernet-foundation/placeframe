from __future__ import annotations

import os
from typing import AsyncGenerator

from fastapi import HTTPException, Request
from models.auth_tables import User
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

if os.environ.get("CODEGEN"):

    async def get_session(request: Request) -> AsyncGenerator[AsyncSession]:
        yield AsyncSession()

else:
    settings = get_settings()

    ApiSessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_api_user}:{settings.database_api_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    AuthSessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_auth_user}:{settings.database_auth_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def get_session(request: Request) -> AsyncGenerator[AsyncSession]:
        claims = getattr(request.state, "claims", {}) or {}
        user_id = claims.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # JIT create user record if it doesn't exist
        async with AuthSessionLocal() as auth_session, auth_session.begin():
            await auth_session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())

        async with ApiSessionLocal() as api_session, api_session.begin():
            if user_id:
                await api_session.execute(func.set_config("app.user_id", str(user_id), True))
            yield api_session
