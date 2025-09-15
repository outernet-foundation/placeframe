# databases.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from common.boto_clients import create_ecs_client, create_secretsmanager_client
from common.database_utils import postgres_cursor
from fastapi import APIRouter, Body, HTTPException, status
from psycopg import sql

from ..settings import Settings, get_settings

router = APIRouter(prefix="/databases")

data_sources_path = Path("/opt/cloudbeaver/workspace/GlobalConfiguration/.dbeaver/data-sources.json")


@router.post("")
def create_database(
    name: str = Body(..., embed=True),
    password_secret_arn: str | None = Body(..., embed=True),
    password_secret_plaintext: str | None = Body(None, embed=True),
):
    if password_secret_arn and password_secret_plaintext:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only one of password_secret_arn or password_secret_plaintext should be provided",
        )
    if not password_secret_arn and not password_secret_plaintext:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "One of password_secret_arn or password_secret_plaintext must be provided"
        )

    if password_secret_plaintext:
        password = password_secret_plaintext
    else:
        assert password_secret_arn is not None
        # Fetch the DB user's password from Secrets Manager using the provided ARN
        try:
            sm = create_secretsmanager_client()
            secret = sm.get_secret_value(SecretId=password_secret_arn)
            password = secret["SecretString"]
        except Exception as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not read password secret: {exc}") from exc

    settings = get_settings()

    # Connect as admin
    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        # Ensure database doesn't already exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is not None:
            if settings.backend == "docker":
                print(f"Database {name} already exists, skipping creation.")
                return
            if settings.backend == "aws":
                raise HTTPException(status.HTTP_409_CONFLICT, f"Database {name} already exists")

        # Create role
        cursor.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(name), sql.Literal(password)))

        # Create database
        cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(name), sql.Identifier(name)))

        # Update CloudBeaver data source
        with data_sources_path.open("r", encoding="utf-8") as file:
            data: Dict[str, Any] = json.load(file)

    data["connections"][name] = {
        "provider": "postgresql",
        "driver": "postgres-jdbc",
        "name": name,
        "save-password": True,
        "configuration": {
            "host": settings.postgres_host,
            "port": "5432",
            "database": name,
            "user": name,
            "password": password,
            "url": f"jdbc:postgresql://{settings.postgres_host}:5432/{name}",
        },
    }

    with data_sources_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    _restart_cloudbeaver(settings)

    return {"message": "created"}


@router.delete("/{name}")
def delete_database(name: str):
    settings = get_settings()

    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        # Ensure database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is None:
            if settings.backend == "docker":
                print(f"Database {name} not found, skipping deletion.")
                return {"message": "deleted"}
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Database {name} not found")

        # Terminate other sessions, then drop db and role
        cursor.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
            """,
            (name,),
        )
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))

        # Load CloudBeaver data sources (mirroring create endpoint's style)
        with data_sources_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)

    # Remove connection entry and persist
    data["connections"].pop(name, None)
    with data_sources_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    _restart_cloudbeaver(settings)

    return {"message": "deleted"}


#
def _restart_cloudbeaver(settings: Settings) -> None:
    try:
        if settings.backend == "docker":
            import docker  # local import to avoid hard dep on AWS hosts

            client = docker.from_env()
            container = client.containers.get(settings.cloudbeaver_service_id)
            container.restart()  # type: ignore[union-attr]
        elif settings.backend == "aws":
            assert settings.ecs_cluster_arn is not None
            create_ecs_client().update_service(
                cluster=settings.ecs_cluster_arn, service=settings.cloudbeaver_service_id, forceNewDeployment=True
            )
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"CloudBeaver restart failed: {exc}") from exc
