from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from common.database_utils import postgres_cursor
from psycopg import sql

from .settings import get_settings


def main():
    settings = get_settings()

    try:
        with postgres_cursor(
            host=settings.postgres_host, user=settings.postgres_admin_user, password=settings.postgres_admin_password
        ) as cursor:
            # Database must not exist
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.database_name,))
            if cursor.fetchone() is not None:
                raise FileExistsError(f"Database already exists: {settings.database_name}")

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
        with data_sources_path.open("rw", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

            data["connections"][settings.database_name] = {
                "provider": "postgresql",
                "driver": "postgres-jdbc",
                "name": settings.database_name,
                "save-password": True,
                "configuration": {
                    "host": settings.postgres_host,
                    "port": "5432",
                    "database": settings.database_name,
                    "url": f"jdbc:postgresql://{settings.postgres_host}:5432/{settings.database_name}",
                    "type": "dev",
                    "configurationType": "MANUAL",
                    "closeIdleConnection": True,
                },
            }

            json.dump(data, f, indent=2)

    except Exception as e:
        print(str(e))
        sys.exit(1)
