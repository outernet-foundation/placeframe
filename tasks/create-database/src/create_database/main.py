from __future__ import annotations

import json
import sys

from common.database_utils import cloudbeaver_gql, cloudbeaver_login, postgres_cursor
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
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(settings.database_name)),
                (settings.database_password,),
            )

            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(settings.database_name), sql.Identifier(settings.database_name)
                )
            )

        # CloudBeaver connection must not exist
        cloudbeaver_api_url, opener = cloudbeaver_login(
            cloudbeaver_url=str(settings.cloudbeaver_url),
            cloudbeaver_admin_user=settings.cloudbeaver_admin_user,
            cloudbeaver_admin_password=settings.cloudbeaver_admin_password,
        )

        # Create CloudBeaver connection
        cloudbeaver_gql(
            opener,
            cloudbeaver_api_url,
            {
                "query": (
                    "mutation C($pid:ID!,$cfg:ConnectionConfig!){"
                    "connection:createConnection(projectId:$pid,config:$cfg){id name}}"
                ),
                "variables": {
                    "pid": "g_GlobalConfiguration",
                    "cfg": {
                        "configurationType": "MANUAL",
                        "driverId": "postgresql",
                        "name": settings.database_name,
                        "host": settings.postgres_host,
                        "port": 5432,
                        "databaseName": settings.database_name,
                        "authModelId": "native",
                        "credentials": {"userName": settings.database_name, "userPassword": settings.database_password},
                        "properties": {},
                    },
                },
            },
        )

        print(json.dumps({"ok": True}))
    except Exception as e:
        print(str(e))
        sys.exit(1)
