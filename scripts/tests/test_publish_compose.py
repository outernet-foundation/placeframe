from scripts.publish_compose import pin_references, substitute_holes

REGISTRY = "ghcr.io/outernet-foundation/placeframe"


def test_substitute_holes_fills_internal_vars_and_keeps_passthroughs():
    text = (
        "services:\n"
        "  api:\n"
        f"    image: {REGISTRY}/api:${{API_SHA}}\n"
        "    environment:\n"
        f"      PUBLIC_URL: ${{PUBLIC_URL:?err}}\n"
        f"      AUTH_ISSUER_URL: ${{AUTH_ISSUER_URL:-}}\n"
        f"      NGROK_IMAGE: ${{NGROK_IMAGE:?err}}\n"
    )

    baked = substitute_holes(text, {"API_SHA": "tree-abc", "NGROK_IMAGE": "mirror/ngrok:alpine@sha256:abc"})

    assert f"{REGISTRY}/api:tree-abc" in baked
    assert "mirror/ngrok:alpine@sha256:abc" in baked
    assert "${PUBLIC_URL:?err}" in baked
    assert "${AUTH_ISSUER_URL:-}" in baked


def test_pin_references_resolves_placeframe_tags_to_digests(monkeypatch):
    monkeypatch.setattr(
        "scripts.publish_compose.resolve_remote_digest",
        lambda _reference: "sha256:" + "f" * 64,
    )
    text = (
        "services:\n"
        f"  api:\n    image: {REGISTRY}/api:tree-abc\n"
        "  loki:\n    image: ghcr.io/outernet-foundation/mirror/docker.io/grafana/loki@sha256:abc\n"
    )

    pinned = pin_references(text, {})

    assert f"{REGISTRY}/api@sha256:" + "f" * 64 in pinned
    assert f"{REGISTRY}/api:tree-abc" not in pinned
    # Non-placeframe references (the org mirror) pass through untouched.
    assert "mirror/docker.io/grafana/loki@sha256:abc" in pinned
    # Resolutions cache across calls — one registry hit per reference.
    digests: dict[str, str] = {}
    pin_references(text, digests)
    assert list(digests) == [f"{REGISTRY}/api:tree-abc"]


def test_pin_references_leaves_hole_texts_alone():
    text = f"services:\n  api:\n    image: {REGISTRY}/api:${{API_SHA}}\n"

    assert pin_references(text, {}) == text
