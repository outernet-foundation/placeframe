# main.py
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from common.boto_clients import create_ecs_client, create_secretsmanager_client
from common.database_utils import postgres_cursor
from psycopg import sql

from .settings import Settings, get_settings

# EFS is mounted at /mnt/efs for the Lambda; the access point root is /opt/cloudbeaver/workspace
# so the GlobalConfiguration path lives directly under /mnt/efs.
data_sources_path = Path("/mnt/efs/GlobalConfiguration/.dbeaver/data-sources.json")


def main(event: Dict[str, Any], _context: Any):
    op = event.get("op")
    name = event.get("name")

    if op not in {"create", "update", "delete"}:
        raise ValueError(f"Invalid op: {op}")
    if not isinstance(name, str) or not name:
        raise ValueError("name is required")

    settings = get_settings()

    if op in {"create", "update"}:
        password_plaintext = event.get("password")
        password_secret_arn = event.get("password_secret_arn")

        if password_plaintext is not None and password_secret_arn is not None:
            raise ValueError("Only one of password or password_secret_arn may be provided")
        if password_plaintext is None and password_secret_arn is None:
            raise ValueError("One of password or password_secret_arn must be provided")

        if password_plaintext is not None:
            if not isinstance(password_plaintext, str):
                raise ValueError("password must be a non-empty string")
            password = password_plaintext
        else:
            assert password_secret_arn is not None
            if not isinstance(password_secret_arn, str):
                raise ValueError("password_secret_arn must be a non-empty string")

            password = create_secretsmanager_client().get_secret_value(SecretId=password_secret_arn)["SecretString"]

        if op == "create":
            _create_database(name=name, password=password, settings=settings)
        elif op == "update":
            _update_database(name=name, password=password, settings=settings)
    else:
        assert op == "delete"
        _delete_database(name=name, settings=settings)


def _create_database(*, name: str, password: str, settings: Settings) -> None:
    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        # Ensure database doesn't already exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is not None:
            if settings.backend == "docker":
                print(f"Database {name} already exists, skipping creation.")
                # still update DS and bounce to ensure DS state correct
            else:
                raise RuntimeError(f"Database {name} already exists")
        else:
            # Create database and role
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(name), sql.Literal(password))
            )
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(name), sql.Identifier(name)))

    _update_cloudbeaver_data_sources(name=name, password=password, settings=settings)


def _update_database(*, name: str, password: str, settings: Settings) -> None:
    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        # Ensure database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is None:
            raise RuntimeError(f"Database {name} does not exist")

        # Update role password
        cursor.execute(sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(sql.Identifier(name), sql.Literal(password)))

    # Update data source with new password
    _update_cloudbeaver_data_sources(name=name, password=password, settings=settings)

    # Terminate old sessions for role so new password is enforced immediately
    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        cursor.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE usename = %s AND pid <> pg_backend_pid()
            """,
            (name,),
        )


def _delete_database(*, name: str, settings: Settings) -> None:
    # Remove data source
    _update_cloudbeaver_data_sources(name=name, password=None, settings=settings)

    # Drop database and role
    with postgres_cursor(
        host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
    ) as cursor:
        cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def _update_cloudbeaver_data_sources(*, name: str, password: str | None, settings: Settings) -> None:
    with data_sources_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if password is None:
        data["connections"].pop(name, None)
    else:
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

    with data_sources_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    if settings.backend == "docker":
        import docker  # local import

        client = docker.from_env()
        container = client.containers.get(settings.cloudbeaver_service_id)
        container.restart()  # type: ignore[union-attr]

        # naive wait until 'running'
        deadline = time.time() + 120
        while time.time() < deadline:
            container.reload()
            if getattr(container, "status", "") == "running":
                return
            time.sleep(2)
        raise RuntimeError("CloudBeaver did not become running (docker) in time")

    elif settings.backend == "aws":
        assert settings.ecs_cluster_arn is not None
        ecs = create_ecs_client()
        ecs.update_service(
            cluster=settings.ecs_cluster_arn, service=settings.cloudbeaver_service_id, forceNewDeployment=True
        )
        waiter = ecs.get_waiter("services_stable")
        waiter.wait(
            cluster=settings.ecs_cluster_arn,
            services=[settings.cloudbeaver_service_id],
            WaiterConfig={"Delay": 5, "MaxAttempts": 120},
        )
    else:
        raise RuntimeError(f"Unknown backend: {settings.backend}")
