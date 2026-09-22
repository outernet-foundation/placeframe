from pathlib import Path

import yaml

from build_scripts.placeframe.ci.publish_compose import _inline_configs  # noqa: PLC2701 — testing private helper


def test_inline_configs_replaces_file_with_escaped_content(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("loki.yaml").write_text("storage:\n  access_key_id: ${S3_ACCESS_KEY}\n", encoding="utf-8")
    baked = Path("compose.yml")
    baked.write_text(
        "services:\n"
        "  loki:\n"
        "    image: ghcr.io/outernet-foundation/mirror/docker.io/grafana/loki@sha256:abc\n"
        "configs:\n"
        "  loki_config:\n"
        "    file: loki.yaml\n",
        encoding="utf-8",
    )

    _inline_configs(baked)

    document = yaml.safe_load(baked.read_text(encoding="utf-8"))
    assert document["services"]["loki"]["image"] == (
        "ghcr.io/outernet-foundation/mirror/docker.io/grafana/loki@sha256:abc"
    )
    assert document["configs"]["loki_config"] == {"content": "storage:\n  access_key_id: $${S3_ACCESS_KEY}\n"}


def test_inline_configs_keeps_documents_without_configs_untouched(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    baked = Path("compose.yml")
    baked.write_text("services:\n  postgres:\n    image: db:16\n", encoding="utf-8")

    _inline_configs(baked)

    assert baked.read_text(encoding="utf-8") == "services:\n  postgres:\n    image: db:16\n"
