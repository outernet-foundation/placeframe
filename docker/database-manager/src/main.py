# main.py
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from copy import deepcopy

# main.py
from importlib.resources import files as pkg_files
from pathlib import Path
from typing import Any, LiteralString, cast

from common.boto_clients import create_ecs_client, create_secretsmanager_client
from psycopg import Cursor
from psycopg.sql import SQL, Identifier, Literal
from typer import Exit, Option, run

from .database_utils import postgres_cursor
from .settings import Settings, get_settings


def _read_sql(name: str) -> str:
    # sql is a subpackage beside this module
    return pkg_files(f"{__package__}.sql").joinpath(name).read_text(encoding="utf-8")


workspace_directory = Path("/mnt/efs")
data_sources_path = workspace_directory / "GlobalConfiguration/.dbeaver/data-sources.json"


def main(event: dict[str, Any], _context: Any):
    op = event.get("op")
    name = event.get("name")

    if op not in {"create", "update", "delete"}:
        raise ValueError(f"Invalid op: {op}")
    if not isinstance(name, str) or not name:
        raise ValueError("name is required")

    settings = get_settings()

    if op in {"create", "update"}:
        owner_password = _get_role_password(event, "owner")
        api_user_password = _get_role_password(event, "api_user")
        auth_user_password = _get_role_password(event, "auth_user")
        orchestration_user_password = _get_role_password(event, "orchestration_user")

        if op == "create":
            _create_database(
                settings, name, owner_password, api_user_password, auth_user_password, orchestration_user_password
            )
        else:
            assert op == "update"
            _update_database(
                settings, name, owner_password, api_user_password, auth_user_password, orchestration_user_password
            )
    else:
        assert op == "delete"
        _delete_database(settings, database_name=name)


def _create_database(
    settings: Settings,
    database_name: str,
    owner_password: str,
    api_user_password: str,
    auth_user_password: str,
    orchestration_user_password: str,
):
    owner = f"{database_name}_owner"
    api_user = f"{database_name}_api_user"
    auth_user = f"{database_name}_auth_user"
    orchestration_user = f"{database_name}_orchestration_user"

    # Ensure database exists
    if _database_exists(settings, database_name):
        print(f"Database {database_name} already exists, skipping creation")
    else:
        with postgres_cursor(
            "postgres", settings.postgres_host, settings.postgres_admin_user, settings.postgres_admin_password
        ) as cursor:
            print(f"Creating database {database_name}")

            # Creating a database must run outside a transaction
            with autocommit(cursor):
                cursor.execute(
                    SQL("CREATE DATABASE {} OWNER {};").format(
                        Identifier(database_name), Identifier(settings.postgres_admin_user)
                    )
                )

    _put_roles(
        settings,
        database_name,
        owner,
        api_user,
        auth_user,
        orchestration_user,
        owner_password,
        api_user_password,
        auth_user_password,
        orchestration_user_password,
    )


def _update_database(
    settings: Settings,
    database_name: str,
    owner_password: str,
    api_user_password: str,
    auth_user_password: str,
    orchestration_user_password: str,
):
    owner = f"{database_name}_owner"
    api_user = f"{database_name}_api_user"
    auth_user = f"{database_name}_auth_user"
    orchestration_user = f"{database_name}_orchestration_user"

    if not _database_exists(settings, database_name):
        raise RuntimeError(f"Database {database_name} does not exist")

    _put_roles(
        settings,
        database_name,
        owner,
        api_user,
        auth_user,
        orchestration_user,
        owner_password,
        api_user_password,
        auth_user_password,
        orchestration_user_password,
    )


def _delete_database(settings: Settings, database_name: str) -> None:
    # Remove CloudBeaver entry first (no-op if already absent)
    _update_cloudbeaver(settings, database_name)

    with postgres_cursor(
        "postgres", settings.postgres_host, settings.postgres_admin_user, settings.postgres_admin_password
    ) as cursor:
        print(f"Dropping database {database_name}")

        # Dropping a database must run outside a transaction
        with autocommit(cursor):
            # Tolerates already-missing DB and terminates active sessions
            cursor.execute(SQL("DROP DATABASE IF EXISTS {} WITH (FORCE);").format(Identifier(database_name)))

        # Drop roles if present (reverse order of creation)
        cursor.execute(SQL("DROP ROLE IF EXISTS {};").format(Identifier(f"{database_name}_auth_user")))
        cursor.execute(SQL("DROP ROLE IF EXISTS {};").format(Identifier(f"{database_name}_api_user")))
        cursor.execute(SQL("DROP ROLE IF EXISTS {};").format(Identifier(f"{database_name}_owner")))

    _update_cloudbeaver(settings, database_name)


def _get_role_password(event: dict[str, Any], role_name: str):
    password_plaintext = event.get(f"{role_name}_password")
    password_secret_arn = event.get(f"{role_name}_password_secret_arn")

    if password_plaintext is not None and password_secret_arn is not None:
        raise ValueError(f"Only one of {role_name}_password or {role_name}_password_secret_arn may be provided")
    if password_plaintext is None and password_secret_arn is None:
        raise ValueError(f"One of {role_name}_password or {role_name}_password_secret_arn must be provided")

    if password_plaintext is not None:
        if not isinstance(password_plaintext, str):
            raise ValueError(f"{role_name}_password must be a non-empty string")
        return password_plaintext
    else:
        assert password_secret_arn is not None
        if not isinstance(password_secret_arn, str):
            raise ValueError(f"{role_name}_password_secret_arn must be a non-empty string")

        return create_secretsmanager_client().get_secret_value(SecretId=password_secret_arn)["SecretString"]


def _database_exists(settings: Settings, database_name: str):
    with postgres_cursor(
        "postgres", settings.postgres_host, settings.postgres_admin_user, settings.postgres_admin_password
    ) as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        return cursor.fetchone() is not None


@contextmanager
def autocommit(cursor: Cursor):
    prev = cursor.connection.autocommit
    try:
        cursor.connection.autocommit = True
        yield
    finally:
        cursor.connection.autocommit = prev


def _put_roles(
    settings: Settings,
    database_name: str,
    owner: str,
    api_user: str,
    auth_user: str,
    orchestration_user: str,
    owner_password: str,
    api_user_password: str,
    auth_user_password: str,
    orchestration_user_password: str,
):
    # Connect to default "postgres" database to create/update roles
    with postgres_cursor(
        "postgres", settings.postgres_host, settings.postgres_admin_user, settings.postgres_admin_password
    ) as cursor:
        print(f"Creating roles for database {database_name}")

        # Ensure roles exist and have correct passwords
        cursor.execute(
            SQL(cast(LiteralString, _read_sql("put_roles.template.sql"))).format(
                owner=Identifier(owner),
                owner_literal=Literal(owner),
                owner_password=Literal(owner_password),
                api_user=Identifier(api_user),
                api_user_literal=Literal(api_user),
                api_user_password=Literal(api_user_password),
                auth_user=Identifier(auth_user),
                auth_user_literal=Literal(auth_user),
                auth_user_password=Literal(auth_user_password),
                orchestration_user=Identifier(orchestration_user),
                orchestration_user_literal=Literal(orchestration_user),
                orchestration_user_password=Literal(orchestration_user_password),
                database=Identifier(database_name),
                database_literal=Literal(database_name),
            )
        )

    # Connect to new database to configure role privileges
    with postgres_cursor(
        database_name, settings.postgres_host, settings.postgres_admin_user, settings.postgres_admin_password
    ) as cursor:
        print(f"Configuring privileges for database {database_name}")

        cursor.execute(
            SQL(cast(LiteralString, _read_sql("configure_database.template.sql"))).format(
                database=Identifier(database_name),
                owner=Identifier(owner),
                api_user=Identifier(api_user),
                auth_user=Identifier(auth_user),
                orchestration_user=Identifier(orchestration_user),
                auth_schema=Identifier("auth"),
            )
        )

    _update_cloudbeaver(settings, database_name, owner, owner_password)


def _update_cloudbeaver(settings: Settings, database_name: str, user: str | None = None, password: str | None = None):
    if settings.cloudbeaver_service_id is None:
        print("CLOUDBEAVER_SERVICE_ID not set, skipping CloudBeaver update")
        return

    # Load current state
    with data_sources_path.open("r", encoding="utf-8") as fh:
        current_data = json.load(fh)

    new_data = deepcopy(current_data)
    new_data.setdefault("connections", {})

    if user is None:
        new_data["connections"].pop(database_name, None)
    else:
        if password is None:
            raise ValueError("password must be provided if user is provided")

        new_data["connections"][database_name] = {
            "provider": "postgresql",
            "driver": "postgres-jdbc",
            "name": database_name,
            "save-password": True,
            "configuration": {
                "host": settings.postgres_host,
                "port": "5432",
                "database": database_name,
                "user": user,
                "password": password,
                "url": f"jdbc:postgresql://{settings.postgres_host}:5432/{database_name}",
            },
        }

    if new_data == current_data:
        print("No changes to CloudBeaver data sources, skipping update.")
        return

    # Persist and restart CloudBeaver
    with data_sources_path.open("w", encoding="utf-8") as fh:
        json.dump(new_data, fh, indent=2)
        fh.write("\n")

    print("Updated CloudBeaver data sources, restarting service")

    if settings.backend == "docker":
        import docker  # local import

        client = docker.from_env()  # type: ignore[call-arg]
        container = client.containers.get(settings.cloudbeaver_service_id)  # type: ignore[call-arg]
        container.restart()  # type: ignore[union-attr]

        print("Waiting for CloudBeaver service to restart")
        deadline = time.time() + 120
        while time.time() < deadline:
            container.reload()  # type: ignore[union-attr]
            if getattr(container, "status", "") == "running":  # type: ignore[union-attr]
                return
            time.sleep(2)
        raise RuntimeError("Timeout waiting for CloudBeaver service to restart")

    else:
        assert settings.backend == "aws"
        assert settings.ecs_cluster_arn is not None
        ecs = create_ecs_client()
        ecs.update_service(
            cluster=settings.ecs_cluster_arn, service=settings.cloudbeaver_service_id, forceNewDeployment=True
        )

        print("Waiting for CloudBeaver service to restart")
        waiter = ecs.get_waiter("services_stable")
        waiter.wait(
            cluster=settings.ecs_cluster_arn,
            services=[settings.cloudbeaver_service_id],
            WaiterConfig={"Delay": 5, "MaxAttempts": 120},
        )

    print("Done")


def cli(
    op: str = Option(..., "--op", help="create | update | delete", case_sensitive=False),
    name: str = Option(..., "--name", help="Database name"),
    owner_password: str = Option(..., "--owner-password", help="Owner role password"),
    api_user_password: str = Option(..., "--api-user-password", help="API user role password"),
    auth_user_password: str = Option(..., "--auth-user-password", help="Auth user role password"),
    orchestration_user_password: str = Option(
        ..., "--orchestration-user-password", help="Orchestration user role password"
    ),
):
    if op.lower() != "create":
        print(f"op='{op}' not implemented; no-op.")
        raise Exit(code=0)

    main(
        {
            "op": "create",
            "name": name,
            "owner_password": owner_password,
            "api_user_password": api_user_password,
            "auth_user_password": auth_user_password,
            "orchestration_user_password": orchestration_user_password,
        },
        None,
    )


if __name__ == "__main__":
    run(cli)
