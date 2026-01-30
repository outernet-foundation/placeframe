from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal

import typer
import yaml
from common.run_command import run_command

SHARED_LOCK = Path(".env.lock")
LOCAL_LOCK = Path(".env.local.lock")
COMPOSE_FILE = Path("compose.yml")
BAKE_FILE = Path("compose.bake.yml")
METADATA_PATH = Path("metadata.json")

Mode = Literal["local", "ci"]
Gpu = Literal["auto", "cpu", "cuda", "rocm", "all"]

app = typer.Typer(add_completion=False)


def _load_lock_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        (p := line.split("=", 1))[0].strip(): p[1].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.startswith("#")
    }


def _write_lock_file(path: Path, variables: dict[str, str], header: str = "Generated") -> None:
    content = f"# {header} by lock.py\n" + "\n".join(f"{k}={v}" for k, v in sorted(variables.items())) + "\n"
    path.write_text(content, encoding="utf-8")


def _inspect_image(image_ref: str, log_error: bool = False) -> str | None:
    try:
        output = run_command(
            f"docker buildx imagetools inspect {image_ref}", stream_log=False, log=False, verbose_errors=False
        )
        match = re.search(r"^Digest:\s+(sha256:[a-f0-9]+)", output, re.MULTILINE)
        if match:
            return match.group(1)
    except subprocess.CalledProcessError as e:
        if log_error:
            print(f"    [ERROR] Failed to resolve {image_ref}. Check network/permissions.")
            if e.stderr:
                print(f"    Details: {e.stderr.strip()}")
    return None


def _get_remote_digest(image_ref: str) -> str:
    if "$" in image_ref:
        return ""

    print(f"    Querying registry for {image_ref}...")
    digest = _inspect_image(image_ref, log_error=True)
    if not digest:
        raise RuntimeError(f"Could not resolve digest for required image: {image_ref}")
    return digest


def _check_gc_limits(min_gb: int = 60) -> None:
    candidates = [Path("/etc/docker/daemon.json"), Path(os.path.expanduser("~/.docker/daemon.json"))]
    if "WSL_DISTRO_NAME" in os.environ:
        try:
            win_home = run_command('wslpath $(cmd.exe /c "echo %UserProfile%" 2>/dev/null)', log=False).strip()
            candidates.append(Path(win_home) / ".docker" / "daemon.json")
        except Exception:
            pass

    config = next((p for p in candidates if p.exists() and os.access(p, os.R_OK)), None)
    if not config:
        print(f"    [WARN] No readable daemon.json found. Ensure defaultKeepStorage > {min_gb}GB.")
        return

    data = json.loads(config.read_text())
    raw = data.get("builder", {}).get("gc", {}).get("defaultKeepStorage")
    if not raw:
        raise RuntimeError(f"Missing 'builder.gc.defaultKeepStorage' in {config}. Docker defaults are too low.")

    m = re.match(r"^(\d+(?:\.\d+)?)\s*([TGMK]i?B)?$", str(raw), re.IGNORECASE)
    if not m:
        raise RuntimeError(f"Could not parse 'defaultKeepStorage' value: {raw}")

    mult = {"T": 1024, "G": 1, "M": 1 / 1024, "K": 1 / 1024**2, "B": 1 / 1024**3}
    unit = (m.group(2) or "B")[0].upper()
    val = float(m.group(1)) * mult.get(unit, 1 / 1024**3)

    if val < min_gb:
        raise RuntimeError(
            f"UNSAFE GC LIMIT: {val:.1f}GB in {config} (Required: {min_gb}GB). RESTART DOCKER AFTER FIXING."
        )

    print(f"    [OK] Docker GC Limit verified: {val:.1f}GB")


def _resolve_targets(targets: list[str] | None, group: str | None, mode: Mode, gpu: Gpu):
    all_images = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8")).get("services", {})
    first_party_images = {name: config for name, config in all_images.items() if config.get("x-image-ref")}

    if targets:
        invalid = [t for t in targets if t not in first_party_images]
        if invalid:
            raise typer.BadParameter(f"Targets not found or not first-party: {', '.join(invalid)}")
        return {name: first_party_images[name] for name in targets}

    if group and group != "base":
        profile = group
    elif mode == "ci" and gpu == "auto":
        profile = "all"
    elif gpu != "auto":
        profile = gpu
    elif shutil.which("nvidia-smi"):
        run_command("nvidia-smi", stream_log=False, log=False, verbose_errors=False)
        profile = "cuda"
    elif shutil.which("rocminfo"):
        run_command("rocminfo", stream_log=False, log=False, verbose_errors=False)
        profile = "rocm"
    else:
        profile = None

    if profile == "all":
        return first_party_images

    selected = {
        name: config
        for name, config in first_party_images.items()
        if not config.get("profiles") or (profile and profile in config.get("profiles", []))
    }
    return selected


def _bake_targets(
    target_images: dict[str, Any],
    bake_data: dict[str, Any],
    no_cache: bool,
    progress: str,
    mode: Mode,
    builder: str,
    gpu: Gpu,  # Must be passed in from lock()
) -> None:
    METADATA_PATH.unlink(missing_ok=True)
    bake_targets = [n for n in target_images if n in bake_data.get("services", {})]
    if not bake_targets:
        return

    is_ci = mode == "ci"

    # LOGICAL FIX 1: Namespace the GHA scope by GPU type.
    # Without this, ROCm build overwrites CUDA's cache on every run.
    scope_name = f"plerion-{gpu}"

    c_from: list[str] = []

    if is_ci:
        c_from.append(f"type=gha,scope={scope_name}")

    if not is_ci and builder != "default":
        Path(".buildkit-cache").mkdir(exist_ok=True)
        c_from.append("type=local,src=.buildkit-cache")

    # Reading from all registry caches is safe (fallback warehouse)
    for section in ["x-cache-cuda", "x-cache-rocm"]:
        for entry in bake_data.get(section, {}).get("cache_from", []):
            ctype, ref = _parse_cache_entry(entry)
            if ctype == "registry" and ref:
                if is_ci or _inspect_image(ref):
                    c_from.append(f"type=registry,ref={ref}")

    # --- Setup Cache Destinations (Writes) ---
    c_to_list: list[str] = []

    if is_ci:
        c_to_list.append(f"type=gha,mode=max,scope={scope_name}")

    if not is_ci and builder != "default":
        c_to_list.append("type=local,dest=.buildkit-cache,mode=max")

    # LOGICAL FIX 2: Only write to the registry matching the current GPU build.
    # Without this, CUDA builds corrupt the ROCm cache and vice versa.
    if is_ci:
        if gpu == "cuda":
            relevant_sections = ["x-cache-cuda"]
        elif gpu == "rocm":
            relevant_sections = ["x-cache-rocm"]
        else:
            relevant_sections = []

        for section in relevant_sections:
            for entry in bake_data.get(section, {}).get("cache_to", []):
                ctype, ref = _parse_cache_entry(entry)
                if ctype == "registry" and ref:
                    c_to_list.append(f"type=registry,ref={ref},mode=max,image-manifest=true,oci-mediatypes=true")

    cmd = [
        "docker buildx bake",
        f"-f {BAKE_FILE}",
        f"--metadata-file {METADATA_PATH}",
        f"--progress {progress}",
        "--provenance=false",
        "--sbom=false",
    ]

    # SYNTAX FIX: Each cache entry needs its own --set flag.
    # Joining with commas creates malformed entries.
    for cf in c_from:
        cmd.append(f"--set *.cache-from+={cf}")
    for ct in c_to_list:
        cmd.append(f"--set *.cache-to+={ct}")

    if no_cache:
        cmd.append("--no-cache")
    if mode == "ci":
        cmd.append("--push")
    if mode == "local":
        cmd.append("--load")
    cmd.extend(bake_targets)

    print(f"\nBaking images (Targets: {len(bake_targets)} | GPU: {gpu} | Scope: {scope_name})...")
    run_command(" ".join(cmd), stream_log=True)


def _parse_cache_entry(entry: str | dict[str, str]) -> tuple[str | None, str | None]:
    ctype: str | None = None
    ref: str | None = None
    if isinstance(entry, dict):
        ctype = entry.get("type")
        ref = entry.get("ref")
    else:
        parts: dict[str, str] = {}
        for part in entry.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                parts[k.strip()] = v.strip()
        ctype = parts.get("type")
        ref = parts.get("ref")
    return ctype, ref


@app.command()
def lock(
    upgrade: bool = typer.Option(False, "--upgrade", "-u", help="Re-resolve and rewrite base digests."),
    mode: Mode = typer.Option("local", "--mode", help="local: updates .env.lock.local; ci: updates .env.lock."),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cpu|cuda|rocm|all"),
    progress: str = typer.Option("auto", "--progress", help="Buildx progress mode."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force rebuild by disabling cache usage."),
    group: str | None = typer.Option(None, "--group", help="Bake group/profile to build."),
    targets: list[str] = typer.Option(None, "--target", help="Bake target(s) to build. Overrides --group."),
) -> None:
    if not COMPOSE_FILE.exists():
        raise RuntimeError(f"Compose file not found: {COMPOSE_FILE}")
    if not BAKE_FILE.exists():
        raise RuntimeError(f"Build definition file not found at: {BAKE_FILE}")

    if mode == "local":
        _check_gc_limits(min_gb=60)

    # 1. Load State
    shared_locks = _load_lock_file(SHARED_LOCK)

    # Init current state
    if mode == "local":
        current_state = _load_lock_file(LOCAL_LOCK)
        if not current_state:
            current_state = dict(shared_locks)
        # Ensure we haven't lost keys if the shared lock was updated
        for k, v in shared_locks.items():
            if k not in current_state:
                current_state[k] = v
    else:
        current_state = dict(shared_locks)

    # 2. Resolve Base Images (Always from Shared Contract)
    print("Resolving base image dependencies...")
    bake_data = yaml.safe_load(BAKE_FILE.read_text(encoding="utf-8"))
    bases_updated = False

    for var, ref in bake_data["x-base-images"].items():
        if upgrade or var not in shared_locks:
            digest = _get_remote_digest(ref)
            digest_val = f"@{digest}"
            shared_locks[var] = digest_val
            current_state[var] = digest_val
            bases_updated = True
            print(f"  + {var} -> {digest[:12]}")
        else:
            current_state[var] = shared_locks[var]
            print(f"  [kept] {var}")

    if bases_updated:
        print(f"  [INFO] Updating shared {SHARED_LOCK} with new base digests...")
        _write_lock_file(SHARED_LOCK, shared_locks, "Shared Contract")

    # 3. Bake (Only builds what we asked for)
    os.environ.update(current_state)
    target_images = _resolve_targets(targets, group, mode, gpu)
    _bake_targets(target_images, bake_data, no_cache, progress, mode, "default", gpu)

    # 4. Resolve Runtime Digests (Must resolve EVERYTHING in compose.yml)
    print("\nResolving runtime images...")
    build_images_metadata: dict[str, Any] = json.loads(METADATA_PATH.read_text()) if METADATA_PATH.exists() else {}

    # Load ALL services, not just targets, to ensure the lockfile is complete
    all_compose_services = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8")).get("services", {})
    all_first_party = {name: config for name, config in all_compose_services.items() if config.get("x-image-ref")}

    for name, config in all_first_party.items():
        image_ref = config["x-image-ref"]
        lock_var = f"{name.upper().replace('-', '_')}_IMAGE"

        # Priority 1: Use the freshly built digest
        if name in build_images_metadata:
            digest = build_images_metadata[name]["containerimage.digest"]
            current_state[lock_var] = f"{image_ref}@{digest}"
            print(f"  + {name} (local build) -> {digest[:12]}")
            continue

        # Priority 2: Use existing local/shared lock value (Skip network check)
        # Only strict skip if we are NOT upgrading.
        if not upgrade and lock_var in current_state:
            # If it's a target we *tried* to build but failed/skipped? No, bake would have failed.
            # This handles "ignored" profiles (like ROCm on a CUDA machine).
            print(f"  [kept] {name}")
            continue

        # Priority 3: Must resolve remotely (First run or Upgrade)
        # We HAVE to do this or 'docker compose up' will crash on missing variable.
        try:
            digest = _get_remote_digest(image_ref)
            current_state[lock_var] = f"{image_ref}@{digest}"
            print(f"  + {name} (remote) -> {digest[:12]}")
        except RuntimeError:
            # Fallback for Bootstrap Scenario:
            # If the image doesn't exist remotely (e.g. rename) and we aren't building it
            # (e.g. wrong hardware profile), we must set SOMETHING or Compose crashes.
            if name not in target_images:
                print(f"  [WARN] Could not resolve {name} (remote). Using insecure tag to satisfy Compose.")
                current_state[lock_var] = image_ref
            else:
                # If we targeted it (tried to build it) and it failed, we shouldn't mask the error.
                raise

    # 5. Write Final Lock
    if mode == "ci":
        print(f"\n[CI MODE] Updating shared {SHARED_LOCK} with official digests...")
        _write_lock_file(SHARED_LOCK, current_state, "Shared Contract")
    else:
        print(f"\n[LOCAL MODE] Writing digests to {LOCAL_LOCK}...")
        _write_lock_file(LOCAL_LOCK, current_state, "Local Build State")
        print("  Run 'uv run up' to use this lockfile.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
