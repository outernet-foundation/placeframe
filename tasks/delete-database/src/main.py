from __future__ import annotations

import json
import sys

from common.database_utils import cloudbeaver_gql, cloudbeaver_list_connections, cloudbeaver_login, postgres_cursor
from psycopg import sql

from .settings import get_settings

if __name__ == "__main__":
    settings = get_settings()

    try:
        # CloudBeaver connection must exist
        cloudbeaver_api_url, opener = cloudbeaver_login(
            cloudbeaver_url=str(settings.cloudbeaver_url),
            cloudbeaver_admin_user=settings.cloudbeaver_admin_user,
            cloudbeaver_admin_password=settings.cloudbeaver_admin_password,
        )
        connections_list = cloudbeaver_list_connections(opener, cloudbeaver_api_url)
        connection_id: str | None = next(
            (c["id"] for c in connections_list if c["name"] == settings.database_name), None
        )
        if connection_id is None:
            raise FileNotFoundError(f"CloudBeaver connection not found for database: {settings.database_name}")

        # Delete CloudBeaver connection
        cloudbeaver_gql(
            opener,
            cloudbeaver_api_url,
            {
                "query": "mutation D($pid:ID!,$id:ID!){deleteConnection(projectId:$pid,connectionId:$id)}",
                "variables": {"pid": "g_GlobalConfiguration", "id": connection_id},
            },
        )

        with postgres_cursor(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_admin_user,
            password=settings.postgres_admin_password,
        ) as cursor:
            # Database must exist (it's an invariant violation if not)
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.database_name,))
            if cursor.fetchone() is None:
                raise RuntimeError(f"Unexpected error, database not found: {settings.database_name}")

            # Drop database and role
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (settings.database_name,),
            )
            cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(settings.database_name)))
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(settings.database_name)))

        print(json.dumps({"ok": True}))
    except Exception as e:
        print(str(e))
        sys.exit(1)
