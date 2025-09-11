from __future__ import annotations

import json
from contextlib import contextmanager
from http.cookiejar import CookieJar
from typing import Any
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener

from fastapi import HTTPException
from psycopg import connect

# Helpers


@contextmanager
def postgres_cursor(database_name: str = "postgres", *, host: str, port: int, user: str, password: str):
    with connect(
        host=host, port=port, dbname=database_name, user=user, password=password, connect_timeout=5
    ) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            yield cursor


def cloudbeaver_login(*, cloudbeaver_url: str, cloudbeaver_admin_user: str, cloudbeaver_admin_password: str):
    cloudbeaver_api_url: str = str(cloudbeaver_url).rstrip("/")
    opener: OpenerDirector = build_opener(HTTPCookieProcessor(CookieJar()))

    cloudbeaver_gql(
        opener,
        cloudbeaver_api_url,
        {
            "query": ("mutation L($p:String!,$c:ObjectScalar!){authLogin(provider:$p,credentials:$c){authStatus}}"),
            "variables": {"p": "local", "c": {"user": cloudbeaver_admin_user, "password": cloudbeaver_admin_password}},
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


def cloudbeaver_gql(opener: OpenerDirector, api_url: str, payload: dict[str, Any]):
    with opener.open(
        Request(api_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}),
        timeout=30,
    ) as response:
        body = response.read().decode("utf-8")

    body_json: dict[str, Any] = json.loads(body)

    if body_json.get("errors"):
        raise HTTPException(500, f"Unexpected GraphQL errors: {body_json['errors']}")

    return body_json["data"]
