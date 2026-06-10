from __future__ import annotations

import os
from typing import Any, AsyncGenerator, cast
from uuid import UUID

from datamodels.auth_tables import Tenant, User
from litestar import Request
from litestar.exceptions import ClientException, NotAuthorizedException
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

# Disabled-auth mode pins every anonymous device to one shared tenant so a map captured on one
# phone is visible to another. The nil UUID is a sentinel the personal-tenant trigger's
# gen_random_uuid() can never emit, so it cannot collide with a real personal tenant.
SHARED_ANONYMOUS_TENANT = UUID("00000000-0000-0000-0000-000000000000")

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

        if claims and claims.get("azp") == "placeframe-worker":
            async with OrchestrationSessionLocal() as session, session.begin():
                yield session
            return

        user_id = cast(str | None, claims.get("sub"))

        if not user_id:
            raise NotAuthorizedException("Missing subject claim when creating database session")

        try:
            UUID(user_id)
        except ValueError:
            raise ClientException(
                f"Identity '{user_id}' is not a valid UUID; disabled-auth requires an x-anonymous-identity UUID header"
            ) from None

        auth_disabled = settings.auth_mode == "disabled"

        # JIT create the user (and the shared tenant in disabled mode) if absent
        async with AuthSessionLocal() as auth_session, auth_session.begin():
            if auth_disabled:
                await auth_session.execute(insert(Tenant).values(id=SHARED_ANONYMOUS_TENANT).on_conflict_do_nothing())
            await auth_session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())

        async with ApiSessionLocal() as api_session, api_session.begin():
            await api_session.execute(func.set_config("app.user_id", user_id, True))
            if auth_disabled:
                await api_session.execute(func.set_config("app.tenant_id", str(SHARED_ANONYMOUS_TENANT), True))
            yield api_session
