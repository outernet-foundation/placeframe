from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from common.boto_clients import create_ecs_client
from common.database_utils import postgres_cursor
from psycopg import sql

from .settings import Settings, get_settings


def main(payload: Dict[str, Any] | None = None):
    if payload:
        settings = Settings(**payload)
    else:
        settings = get_settings()

    try:
        with postgres_cursor(
            host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
        ) as cursor:
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.database_name,))
            if cursor.fetchone() is not None:
                if settings.backend == "docker":
                    print(f"Database {settings.database_name} already exists, skipping creation.")
                    return
                if settings.backend == "aws":
                    raise RuntimeError(f"Database {settings.database_name} already exists.")

            print(f"Creating new database: {settings.database_name}")

            # Create role
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(settings.database_name), sql.Literal(settings.database_password)
                )
            )

            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(settings.database_name), sql.Identifier(settings.database_name)
                )
            )

            # Add a new connection to CloudBeaver for the new database
            data_sources_path = Path("/opt/cloudbeaver/workspace/GlobalConfiguration/.dbeaver/data-sources.json")
            with data_sources_path.open("r", encoding="utf-8") as file:
                data: Dict[str, Any] = json.load(file)

            data["connections"][settings.database_name] = {
                "provider": "postgresql",
                "driver": "postgres-jdbc",
                "name": settings.database_name,
                "save-password": True,
                "configuration": {
                    "host": settings.postgres_host,
                    "port": "5432",
                    "database": settings.database_name,
                    "user": settings.database_name,
                    "password": settings.database_password,
                    "url": f"jdbc:postgresql://{settings.postgres_host}:5432/{settings.database_name}",
                },
            }

            with data_sources_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

            # Restart CloudBeaver to pick up new data source
            print("Restarting CloudBeaver to pick up new data source")
            if settings.backend == "docker":
                # use docker sdk to restart cloudbeaver container
                import docker

                client = docker.from_env()
                container = client.containers.get(settings.cloudbeaver_service_id)
                container.restart()  # type: ignore[union-attr]
            elif settings.backend == "aws":
                ecs = create_ecs_client()

                assert settings.ecs_cluster_arn is not None
                ecs.update_service(
                    cluster=settings.ecs_cluster_arn, service=settings.cloudbeaver_service_id, forceNewDeployment=True
                )

    except Exception as e:
        print(str(e))
        sys.exit(1)
