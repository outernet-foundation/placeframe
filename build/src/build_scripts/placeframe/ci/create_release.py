from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import typer
from placeframe_bash import bash, bash_output
from pydantic_settings import BaseSettings

from placeframe_unity.ci_step import ci_step
from ..context_sha import compute_service_shas
from placeframe_unity.git_tags import get_latest_tag_version
from .git_tags import APP_TAG_PREFIXES

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

ARTIFACT_DIR = Path("/tmp/release-artifacts")
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)

GHCR_URL = "https://github.com/orgs/outernet-foundation/packages?repo_name=placeframe"

APP_DISPLAY_NAMES: dict[str, str] = {
    "MapRegistrationTool": "Map Registration Tool",
    "CaptureTool": "Capture Tool",
}

PACKAGES: dict[str, dict[str, str]] = {
    "placeframe-api-client": {"nuget": "PlaceframeApiClient", "npm": "org.nuget.placeframeapiclient"},
    "placeframe-zed-client": {"nuget": "PlaceframeZedClient", "npm": "org.nuget.placeframezedclient"},
    "placeframe-core": {"npm": "org.outernet.placeframe"},
    "placeframe-arfoundation": {"npm": "org.outernet.placeframe.arfoundation"},
    "placeframe-magicleap": {"npm": "org.outernet.placeframe.magicleap"},
}


class Settings(BaseSettings):
    github_repository: str = "outernet-foundation/placeframe"


def _package_artifacts() -> list[Path]:
    assets: list[Path] = []
    if not ARTIFACT_DIR.is_dir():
        print("No release artifacts directory found")
        return assets

    for entry in sorted(ARTIFACT_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if any(entry.name.startswith(p) for p in SKIP_PREFIXES):
            print(f"  Skipping: {entry.name} (not a release artifact)")
            continue
        if any(entry.name.endswith(s) for s in SKIP_SUFFIXES):
            print(f"  Skipping: {entry.name} (not a release artifact)")
            continue

        files = [f for f in entry.rglob("*") if f.is_file()]
        if not files:
            print(f"  Skipping: {entry.name} (empty)")
            continue

        if len(files) == 1:
            asset = ARTIFACT_DIR / f"{entry.name}{files[0].suffix}"
            shutil.copy2(files[0], asset)
            assets.append(asset)
            print(f"  Asset: {asset.name}")
        else:
            zip_path = ARTIFACT_DIR / entry.name
            shutil.make_archive(str(zip_path), "zip", entry)
            asset = zip_path.parent / f"{zip_path.name}.zip"
            assets.append(asset)
            print(f"  Asset: {asset.name} ({len(files)} files)")

    return assets


def _build_release_notes(service_shas: dict[str, str]) -> str:
    lines: list[str] = []

    lines.append("## Docker images")
    lines.append("")
    lines.append(f"Images on [GHCR]({GHCR_URL}), per-service tags:")
    lines.append("")
    lines.append("| Env var | Tag |")
    lines.append("|---|---|")
    for var, sha in sorted(service_shas.items()):
        lines.append(f"| `{var}` | `{sha}` |")
    lines.append("")

    lines.append("## Packages")
    lines.append("")
    lines.append("| Package | Version | Registry |")
    lines.append("|---|---|---|")
    for tag_prefix, registries in PACKAGES.items():
        version = get_latest_tag_version(f"{tag_prefix}-v") or "—"
        links: list[str] = []
        if "nuget" in registries:
            name = registries["nuget"]
            url = f"https://www.nuget.org/packages/{name}/{version}" if version != "—" else ""
            links.append(f"[NuGet]({url})" if url else "NuGet")
        if "npm" in registries:
            name = registries["npm"]
            url = f"https://www.npmjs.com/package/{name}/v/{version}" if version != "—" else ""
            links.append(f"[npm]({url})" if url else "npm")
        display = list(registries.values())[0]
        lines.append(f"| {display} | {version} | {', '.join(links)} |")

    for app_name, tag_prefix in APP_TAG_PREFIXES.items():
        version = get_latest_tag_version(f"{tag_prefix}-v")
        if version:
            display = APP_DISPLAY_NAMES.get(app_name, app_name)
            lines.append(f"| {display} | {version} | — |")

    lines.append("")
    return "\n".join(lines)


def _next_release_tag(repo: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = bash_output(
        f"gh release list --repo {repo} --json tagName --jq '[.[].tagName] | map(select(startswith(\"{today}\"))) | length'"
    ).strip()
    count = int(existing) if existing else 0
    return f"{today}.{count + 1}" if count > 0 else today


@app.command()
def main() -> None:
    settings = Settings.model_validate({})
    tag = _next_release_tag(settings.github_repository)

    with ci_step("Compute service SHAs"):
        service_shas = {
            **compute_service_shas(Path.cwd(), Path("compose.bake.yml")),
            **compute_service_shas(Path.cwd(), Path("compose.zed.bake.yml")),
        }
        for var, sha in sorted(service_shas.items()):
            print(f"  {var}={sha}")

    with ci_step("Package artifacts"):
        assets = _package_artifacts()
        if assets:
            print(f"  {len(assets)} asset(s) ready for upload")
        else:
            print("  No build artifacts to attach")

    with ci_step("Create GitHub Release"):
        notes = _build_release_notes(service_shas)
        print(notes)

        asset_args = " ".join(f'"{a}"' for a in assets)
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(notes)
            notes_path = f.name
        bash(
            f"gh release create {tag} --title {tag}"
            f" --notes-file {notes_path}"
            f" --repo {settings.github_repository}"
            f" {asset_args}"
        )
        Path(notes_path).unlink()
        print(f"  Release created: {tag}")
