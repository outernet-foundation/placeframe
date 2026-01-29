from __future__ import annotations

import os
from typing import Any, AsyncGenerator, cast

from datamodels.auth_tables import User
from litestar import Request
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

if os.environ.get("CODEGEN"):

    async def get_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
        yield AsyncSession()

    async def get_worker_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
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

    OrchestrationSessionLocal = async_sessionmaker(
        create_async_engine(
            f"postgresql+psycopg://{settings.database_orchestration_user}:{settings.database_orchestration_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
            future=True,
            echo=False,
            pool_pre_ping=True,
        ),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def get_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
        claims = request.auth

        if claims and claims.get("azp") == "placeframe-worker":
            async with OrchestrationSessionLocal() as session, session.begin():
                yield session
            return

        user_id = cast(str | None, claims.get("sub"))

        if not user_id:
            raise NotAuthorizedException("Missing subject claim when creating database session")

        # JIT create user record if it doesn't exist
        async with AuthSessionLocal() as auth_session, auth_session.begin():
            await auth_session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())

        async with ApiSessionLocal() as api_session, api_session.begin():
            await api_session.execute(func.set_config("app.user_id", user_id, True))
            yield api_session

    async def get_worker_session(request: Request[str, dict[str, Any], Any]) -> AsyncGenerator[AsyncSession]:
        claims = request.auth

        if not claims or claims.get("azp") != "placeframe-worker":
            raise PermissionDeniedException("Internal use only")

        async for session in get_session(request):
            yield session
