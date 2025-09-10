from __future__ import annotations

import base64
import json
import secrets
from contextlib import contextmanager
from http.cookiejar import CookieJar
from typing import Any
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener

from fastapi import APIRouter, Body, HTTPException
from nacl.public import PublicKey, SealedBox
from psycopg import connect, sql

from ..settings import get_settings

router = APIRouter(prefix="/databases", tags=["databases"])


####
@router.post("")
def create_database(
    name: str = Body(..., embed=True),
    password_public_key_b64: str = Body(..., embed=True),
):
    settings = get_settings()

    with postgres_cursor() as cursor:
        # Database must not exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is not None:
            raise HTTPException(409, f"Database already exists: {name}")

        password: str = secrets.token_urlsafe(32)

        # Create role
        cursor.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(name)),
            (password,),
        )

        # Create database
        cursor.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(name),
                sql.Identifier(name),
            )
        )

    # CloudBeaver connection must not exist
    cloudbeaver_api_url, opener = cloudbeaver_login()

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
                    "name": name,
                    "host": settings.postgres_host,
                    "port": settings.postgres_port,
                    "databaseName": name,
                    "authModelId": "native",
                    "credentials": {
                        "userName": name,
                        "userPassword": password,
                    },
                    "properties": {},
                },
            },
        },
    )

    return {
        "ok": True,
        "encrypted_password": base64.b64encode(
            SealedBox(PublicKey(base64.b64decode(password_public_key_b64))).encrypt(
                password.encode("utf-8")
            )
        ).decode("ascii"),
    }


@router.delete("/{name}")
def destroy_database(name: str):
    # CloudBeaver connection must exist
    cloudbeaver_api_url, opener = cloudbeaver_login()
    connections_list = cloudbeaver_list_connections(opener, cloudbeaver_api_url)
    connection_id: str | None = next(
        (c["id"] for c in connections_list if c["name"] == name),
        None,
    )
    if connection_id is None:
        raise HTTPException(
            404, f"CloudBeaver connection not found for database: {name}"
        )

    # Delete CloudBeaver connection
    cloudbeaver_gql(
        opener,
        cloudbeaver_api_url,
        {
            "query": "mutation D($pid:ID!,$id:ID!){deleteConnection(projectId:$pid,connectionId:$id)}",
            "variables": {
                "pid": "g_GlobalConfiguration",
                "id": connection_id,
            },
        },
    )

    with postgres_cursor() as cursor:
        # Database must exist (it's an invariant violation if not)
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if cursor.fetchone() is None:
            raise HTTPException(500, f"Unexpected error, database not found: {name}")

        # Drop database and role
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

    return {"ok": True}


# Helpers


@contextmanager
def postgres_cursor(database_name: str = "postgres"):
    settings = get_settings()
    with connect(
        host="localhost",
        port=settings.postgres_port,
        dbname=database_name,
        user=settings.postgres_user,
        password=settings.postgres_password,
        connect_timeout=5,
    ) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            yield cursor


def cloudbeaver_login():
    settings = get_settings()
    cloudbeaver_api_url: str = str(settings.cloudbeaver_url).rstrip("/")
    opener: OpenerDirector = build_opener(HTTPCookieProcessor(CookieJar()))

    cloudbeaver_gql(
        opener,
        cloudbeaver_api_url,
        {
            "query": (
                "mutation L($p:String!,$c:ObjectScalar!){"
                "authLogin(provider:$p,credentials:$c){authStatus}}"
            ),
            "variables": {
                "p": "local",
                "c": {
                    "user": settings.cloudbeaver_admin_user,
                    "password": settings.cloudbeaver_admin_password,
                },
            },
        },
    )

    return cloudbeaver_api_url, opener


def cloudbeaver_list_connections(opener: OpenerDirector, cloudbeaver_api_url: str):
    return cloudbeaver_gql(
        opener,
        cloudbeaver_api_url,
        {
            "query": "query Q($pid:ID!){project(projectId:$pid){connections{id name projectId}}}",
            "variables": {"pid": "g_GlobalConfiguration"},
        },
    )["project"]["connections"]


def cloudbeaver_gql(
    opener: OpenerDirector,
    api_url: str,
    payload: dict[str, Any],
):
    with opener.open(
        Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        ),
        timeout=30,
    ) as response:
        body = response.read().decode("utf-8")

    body_json: dict[str, Any] = json.loads(body)

    if body_json.get("errors"):
        raise HTTPException(500, f"Unexpected GraphQL errors: {body_json['errors']}")

    return body_json["data"]
