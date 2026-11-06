import json
import os
import re
import time
from pathlib import Path

from typing import Any

import httpx

TEMPLATE_PATH = Path("/templates/placeframe.json")
READY_TIMEOUT_SECONDS = 600
POLL_INTERVAL_SECONDS = 5
HOLE = re.compile(r"\$\{([A-Z_]+)\}")


def main():
    base_url = os.environ["KEYCLOAK_URL"].rstrip("/")
    username = os.environ.get("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = os.environ["KC_BOOTSTRAP_ADMIN_PASSWORD"]
    realm = render_template()
    print(f"Configuring keycloak realm {realm['realm']} at {base_url}")
    with httpx.Client(timeout=30) as client:
        token = wait_until_ready(client, base_url, username, password)
        sync_realm(client, base_url, token, realm)
        sync_users(client, base_url, token, realm["realm"])
    print("Realm configuration complete")


def render_template() -> dict[str, Any]:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    hole_names = sorted(set(HOLE.findall(template)))
    missing = [name for name in hole_names if not os.environ.get(name, "")]
    if missing:
        raise RuntimeError(f"Realm template holes without an env value: {', '.join(missing)}")
    rendered = template
    for name in hole_names:
        rendered = rendered.replace("${" + name + "}", os.environ[name])
    return json.loads(rendered)


def wait_until_ready(client: httpx.Client, base_url: str, username: str, password: str) -> str:
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while True:
        try:
            token = fetch_admin_token(client, base_url, username, password)
        except (httpx.TransportError, httpx.HTTPStatusError, json.JSONDecodeError, KeyError):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Keycloak admin API not ready within {READY_TIMEOUT_SECONDS}s")
            print("Waiting for keycloak admin API...")
            time.sleep(POLL_INTERVAL_SECONDS)
        else:
            print("Keycloak admin API is ready")
            return token


def fetch_admin_token(client: httpx.Client, base_url: str, username: str, password: str) -> str:
    response = client.post(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli", "username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def sync_realm(client: httpx.Client, base_url: str, token: str, realm: dict[str, Any]) -> None:
    name = realm["realm"]
    lookup = admin_request(client, base_url, token, "GET", f"/admin/realms/{name}", None)
    if lookup.status_code == 404:
        created = admin_request(client, base_url, token, "POST", "/admin/realms", realm)
        if created.status_code != 201:
            raise RuntimeError(f"Realm create failed with HTTP {created.status_code}")
        print(f"Realm {name} created")
        return

    if lookup.status_code != 200:
        raise RuntimeError(f"Realm lookup failed with HTTP {lookup.status_code}")

    updated = admin_request(client, base_url, token, "PUT", f"/admin/realms/{name}", realm)
    if updated.status_code != 204:
        raise RuntimeError(f"Realm update failed with HTTP {updated.status_code}")
    print(f"Realm {name} updated")
    sync_clients(client, base_url, token, name, realm.get("clients", []))


def sync_clients(client: httpx.Client, base_url: str, token: str, realm: str, clients: list[dict[str, Any]]) -> None:
    for client_definition in clients:
        client_id = str(client_definition["clientId"])
        query = f"?clientId={client_id}"
        lookup = admin_request(client, base_url, token, "GET", f"/admin/realms/{realm}/clients{query}", None)
        if lookup.status_code != 200:
            raise RuntimeError(f"Client {client_id} lookup failed with HTTP {lookup.status_code}")

        existing = lookup.json()
        if not existing:
            created = admin_request(
                client, base_url, token, "POST", f"/admin/realms/{realm}/clients", client_definition
            )
            if created.status_code != 201:
                raise RuntimeError(f"Client {client_id} create failed with HTTP {created.status_code}")
            print(f"Client {client_id} created")
            continue

        client_uuid = existing[0]["id"]
        updated = admin_request(
            client, base_url, token, "PUT", f"/admin/realms/{realm}/clients/{client_uuid}", client_definition
        )
        if updated.status_code != 204:
            raise RuntimeError(f"Client {client_id} update failed with HTTP {updated.status_code}")
        print(f"Client {client_id} updated")


def sync_users(client: httpx.Client, base_url: str, token: str, realm: str) -> None:
    seed = os.environ.get("SEED_TEST_USERS", "")
    if not seed:
        return
    for username, password in parse_seed_users(seed):
        query = f"?username={username}&exact=true"
        lookup = admin_request(client, base_url, token, "GET", f"/admin/realms/{realm}/users{query}", None)
        if lookup.status_code != 200:
            raise RuntimeError(f"User {username} lookup failed with HTTP {lookup.status_code}")
        # A fresh 26.8.1 realm's default user profile requires firstName, lastName, and
        # email — a user without any of them fails the first direct grant with
        # "Account is not fully set up" (the implicit verify-profile action).
        user = {
            "username": username,
            "firstName": username.capitalize(),
            "lastName": "Seeded",
            "email": f"{username}@seed.invalid",
            "emailVerified": True,
            "enabled": True,
            "credentials": [{"type": "password", "value": password, "temporary": False}],
        }
        existing = lookup.json()
        if not existing:
            created = admin_request(client, base_url, token, "POST", f"/admin/realms/{realm}/users", user)
            if created.status_code != 201:
                raise RuntimeError(f"User {username} create failed with HTTP {created.status_code}")
            print(f"User {username} created")
        else:
            user_id = existing[0]["id"]
            updated = admin_request(client, base_url, token, "PUT", f"/admin/realms/{realm}/users/{user_id}", user)
            if updated.status_code != 204:
                raise RuntimeError(f"User {username} update failed with HTTP {updated.status_code}")
            print(f"User {username} updated")


def parse_seed_users(seed: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for entry in seed.split(","):
        username, separator, password = entry.partition(":")
        if not separator or not username.strip() or not password:
            raise RuntimeError(f"Invalid SEED_TEST_USERS entry {entry!r}; expected username:password pairs")
        pairs.append((username.strip(), password))
    return pairs


def admin_request(
    client: httpx.Client, base_url: str, token: str, method: str, path: str, payload: object | None
) -> httpx.Response:
    request = client.build_request(method, base_url + path, json=payload)
    request.headers["Authorization"] = f"Bearer {token}"
    return client.send(request)


if __name__ == "__main__":
    main()
