from __future__ import annotations

import os
from typing import Any, AsyncGenerator
from uuid import UUID

from datamodels.auth_tables import Tenant, User
from litestar import Request
from litestar.exceptions import ClientException, NotAuthorizedException
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

        user_id = claims.get("sub") if claims else None

        if not isinstance(user_id, str) or not user_id:
            raise NotAuthorizedException("Missing subject claim when creating database session")

        try:
            UUID(user_id)
        except ValueError:
            raise ClientException(f"Identity '{user_id}' is not a valid UUID") from None

        tenant_id = claims.get("tenant_id") if claims else None

        # JIT create the user (and, when claims carry a tenant, that tenant) if absent
        async with AuthSessionLocal() as auth_session, auth_session.begin():
            if isinstance(tenant_id, str):
                await auth_session.execute(insert(Tenant).values(id=tenant_id).on_conflict_do_nothing())
            await auth_session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())

        async with ApiSessionLocal() as api_session, api_session.begin():
            await api_session.execute(func.set_config("app.user_id", user_id, True))
            if isinstance(tenant_id, str):
                await api_session.execute(func.set_config("app.tenant_id", tenant_id, True))
            yield api_session
