from __future__ import annotations

import os
from typing import Any, AsyncGenerator, cast

from datamodels.auth_tables import User
from litestar import Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

if os.environ.get("CODEGEN"):

    async def get_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
        yield AsyncSession()

else:
    settings = get_settings()

    ApiSessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_api_user}:{settings.database_api_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
            pool_pre_ping=True,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    AuthSessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_auth_user}:{settings.database_auth_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
            pool_pre_ping=True,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def get_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
        claims = request.auth
        user_id = cast(str | None, claims.get("sub"))

        if not user_id:
            raise NotAuthorizedException()

        # JIT create user record if it doesn't exist
        async with AuthSessionLocal() as auth_session, auth_session.begin():
            await auth_session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())

        async with ApiSessionLocal() as api_session, api_session.begin():
            await api_session.execute(func.set_config("app.user_id", user_id, True))
            yield api_session
