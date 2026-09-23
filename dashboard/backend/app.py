"""Dashboard backend: a thin HTTP wrapper around `uv run howard-test`.

Every action the dashboard offers is literally the corresponding `howard-test` subcommand run as
a subprocess with `--json`, executed with cwd set to the placeframe repo root so `uv run` resolves
against *that* workspace (this project deliberately isn't a member of it — see dashboard/AGENTS.md
if that file exists, or the placeframe conversation history that motivated this layout).

Run with (from this directory): uv run uvicorn app:app --reload --port 8010
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, NoReturn

from litestar import Litestar, Request, delete, get, patch, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import NotFoundException
from litestar.response import File, Response

PLACEFRAME_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PLACEFRAME_ROOT / "data"
RECONSTRUCTIONS_DIR = DATA_DIR / "reconstructions"
LOCALIZATIONS_DIR = DATA_DIR / "localizations"
VISUALIZATIONS_DIR = DATA_DIR / "visualizations"
POSELESS_SETS_DIR = DATA_DIR / "poseless_sets"
POSELESS_SETS_INDEX = POSELESS_SETS_DIR / "index.json"
POSELESS_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".insv"}

# This backend runs from its own `uv`-managed venv (dashboard/backend/.venv); without stripping
# VIRTUAL_ENV, the `uv run howard-test` subprocess below inherits it and prints a spurious "doesn't
# match the project environment" warning to stderr on every invocation, polluting the error
# messages callers see when a real failure occurs.
_HOWARD_TEST_ENV = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}

# Wall-clock cap on a background reconstruct job's status-poll loop; mirrors howard_test.py's own
# RECONSTRUCTION_TIMEOUT_S so a stuck reconstruction doesn't poll forever.
RECONSTRUCT_POLL_TIMEOUT_S = 1800.0
RECONSTRUCT_POLL_INTERVAL_S = 3.0

JobKind = Literal["reconstruct", "visualize", "localize"]
JobStatus = Literal["running", "succeeded", "failed"]


@dataclass
class Job:
    id: str
    kind: JobKind
    status: JobStatus = "running"
    reconstruction_id: str | None = None
    run_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


JOBS: dict[str, Job] = {}
# Keep references to in-flight background tasks; asyncio.create_task alone doesn't hold one and
# an unreferenced task can be garbage-collected mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


def _spawn(coro: Any) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


def _run_howard_test_json(*args: str) -> Any:
    result = subprocess.run(
        ["uv", "run", "howard-test", *args, "--json"],
        cwd=PLACEFRAME_ROOT,
        env=_HOWARD_TEST_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    # A reconstruction landing in FAILED/CANCELLED makes the CLI exit 1 *after* printing its JSON
    # payload (see _report_reconstruction in howard_test.py) — that payload, with its `error`
    # field, is exactly what callers want, so a parseable stdout wins regardless of return code.
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    raise RuntimeError(result.stderr.strip() or f"howard-test {' '.join(args)} exited {result.returncode}")


async def _run_howard_test_json_async(*args: str) -> Any:
    return await asyncio.to_thread(_run_howard_test_json, *args)


def _run_howard_test_bytes(*args: str) -> bytes:
    result = subprocess.run(
        ["uv", "run", "howard-test", *args],
        cwd=PLACEFRAME_ROOT,
        env=_HOWARD_TEST_ENV,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(detail or f"howard-test {' '.join(args)} exited {result.returncode}")
    return result.stdout


async def _run_howard_test_bytes_async(*args: str) -> bytes:
    return await asyncio.to_thread(_run_howard_test_bytes, *args)


def _browse_directories(path: str | None, files: str | None = None) -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else Path.home()
    if not target.is_dir():
        raise NotFoundException(f"Not a directory: {target}")
    # `files` is a comma-separated suffix list (e.g. ".tar"); when given, matching files are listed
    # alongside the subdirectories so the same browser can pick a file.
    suffixes = {s.strip().lower() for s in files.split(",") if s.strip()} if files else set()
    try:
        children = sorted(
            (p for p in target.iterdir() if not p.name.startswith(".")),
            key=lambda p: p.name.lower(),
        )
    except PermissionError:
        children = []
    entries = [{"name": p.name, "path": str(p)} for p in children if p.is_dir()]
    file_entries = [
        {"name": p.name, "path": str(p)} for p in children if suffixes and p.is_file() and p.suffix.lower() in suffixes
    ]
    parent = str(target.parent) if target.parent != target else None
    return {"path": str(target), "parent": parent, "entries": entries, "files": file_entries}


# Server-local directory browser for the Localize tab's image-directory picker. A plain
# `<input type=file webkitdirectory>` can't be used here — browsers never expose the absolute
# filesystem path of a picked directory, only a File list with paths relative to the picked root,
# and the CLI this dashboard wraps needs a real absolute path. Since the dashboard always runs on
# the same machine as the CLI (see module docstring), walking the real filesystem server-side and
# returning absolute paths is the direct equivalent of a native picker here.
@get("/api/browse-directories")
async def browse_directories(path: str | None = None, files: str | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(_browse_directories, path, files)


@get("/api/captures")
async def list_captures() -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("captures")


# `stats=false` skips each capture's mono/stereo + frame-count lookup (the API streams through the
# capture tar for those), so the dashboard can draw the tree at once and fill them in afterwards.
@get("/api/reconstructions")
async def list_reconstructions(stats: bool = True) -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("reconstructions", *([] if stats else ["--no-frame-stats"]))


# `cascade=true` also removes what would otherwise block or outlive the delete: the localization
# map (the API refuses while one exists), the local cached tar/PNG, and the local localization runs.
@delete("/api/reconstructions/{reconstruction_id:str}")
async def delete_reconstruction(reconstruction_id: str, cascade: bool = False) -> None:
    # 204 No Content on success; a failure (including the API's "has an associated localization
    # map" refusal — see docker/api/src/routers/reconstructions.py) raises RuntimeError from
    # _run_howard_test_json, which the RuntimeError exception handler turns into a 500 with detail.
    await _run_howard_test_json_async("delete-reconstruction", reconstruction_id, *(["--cascade"] if cascade else []))


@dataclass
class RenameCaptureRequest:
    name: str


# Renames the capture session itself (the API's own name), and keeps a linked image folder's local
# name in step so the row doesn't show two different names for the same thing.
@patch("/api/captures/{capture_id:str}")
async def rename_capture(capture_id: str, data: RenameCaptureRequest) -> dict[str, Any]:
    session = await _run_howard_test_json_async("rename-capture", capture_id, data.name)
    await asyncio.to_thread(_rename_linked_poseless_set, capture_id, data.name)
    return session


def _rename_linked_poseless_set(capture_id: str, name: str) -> None:
    index = _load_poseless_index()
    changed = False
    for entry in index.values():
        if entry.get("capture_session_id") == capture_id:
            entry["name"] = name
            changed = True
    if changed:
        _save_poseless_index(index)


# The capture's tar and row; `cascade=true` deletes its reconstructions (each cascading as above)
# first, which the API otherwise refuses. Also unlinks the image folder that uploaded it, if any,
# so the folder reappears as unlinked rather than pointing at a deleted capture.
@delete("/api/captures/{capture_id:str}")
async def delete_capture(capture_id: str, cascade: bool = False) -> None:
    await _run_howard_test_json_async("delete-capture", capture_id, *(["--cascade"] if cascade else []))
    await asyncio.to_thread(_unlink_poseless_capture, capture_id)


def _unlink_poseless_capture(capture_id: str) -> None:
    index = _load_poseless_index()
    changed = False
    for entry in index.values():
        if entry.get("capture_session_id") == capture_id:
            entry.pop("capture_session_id", None)
            entry.pop("focal_length", None)
            changed = True
    if changed:
        _save_poseless_index(index)


@dataclass
class ImportReconstructionRequest:
    tar_path: str
    # A tar carries one fixed reconstruction id, so importing the same tar twice is refused;
    # new_id imports it again as a separate copy.
    new_id: bool = False


# Uploads a reconstruction tar (metadata.json + artifacts, e.g. from `howard-test`'s export or an
# external pipeline) via `howard-test import-reconstruction`. A direct call rather than a job: the
# upload of a few-hundred-MB tar is seconds, not minutes. The API also creates the reconstruction's
# localization map, so the reconstruction can't be deleted until that map is.
def _resolve_tar(tar_path: str) -> str:
    tar = Path(tar_path).expanduser()
    if not tar.is_file():
        raise ValueError(f"Not a file: {tar}")
    if tar.suffix.lower() != ".tar":
        raise ValueError(f"Not a .tar file: {tar}")
    return str(tar.resolve())


@post("/api/reconstructions/import")
async def import_reconstruction(data: ImportReconstructionRequest) -> dict[str, Any]:
    tar = await asyncio.to_thread(_resolve_tar, data.tar_path)
    return await _run_howard_test_json_async("import-reconstruction", tar, *(["--new-id"] if data.new_id else []))


# Every localization run directory, finished or not. `results.json` (written by the CLI at the end)
# describes a finished run; until then `request.json` (written by start_localize, below) says what
# was asked for and `progress.json` how far it has got. A run with neither a result nor a live job
# was interrupted (e.g. the dashboard restarted mid-run) and is reported as incomplete.
def _run_job(run_id: str) -> Job | None:
    return next((job for job in JOBS.values() if job.kind == "localize" and job.run_id == run_id), None)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


@dataclass
class ImportRequest:
    path: str
    # Only meaningful for a reconstruction tar, which carries a fixed id.
    new_id: bool = False


def _classify_import(path_str: str) -> tuple[str, Path]:
    """What the Import button was pointed at: a folder of images, a reconstruction
    tar, or a spherical video. A video that declares no spherical projection is
    an ordinary video, which nothing here can reconstruct yet."""
    path = Path(path_str).expanduser()
    if path.is_dir():
        return "image_folder", path
    if not path.is_file():
        raise ValueError(f"Not a file or folder: {path}")
    suffix = path.suffix.lower()
    if suffix == ".tar":
        return "reconstruction_tar", path.resolve()
    if suffix in VIDEO_EXTENSIONS:
        projection = _run_howard_test_json("inspect-video", str(path))["projection"]
        if projection is None:
            raise ValueError(
                f"{path.name} is an ordinary (non-spherical) video. Only spherical video is supported so far: "
                "a 360 camera's own file declares its projection, and this one declares none."
            )
        if projection != "EQUIRECTANGULAR":
            raise ValueError(f"{path.name} is a {projection.lower()} video; only equirectangular is supported")
        return "spherical_video", path.resolve()
    raise ValueError(f"Cannot import {path.name}: expected a folder of images, a .tar reconstruction, or a video")


# A folder and a tar are quick; a video is minutes of extraction, upload and
# reconstruction, so it returns a job the tree follows like any reconstruction.
@post("/api/import")
async def import_path(data: ImportRequest) -> dict[str, Any]:
    kind, path = await asyncio.to_thread(_classify_import, data.path)
    if kind == "image_folder":
        return {"kind": kind, "image_set": await asyncio.to_thread(_register_poseless_set, str(path))}
    if kind == "reconstruction_tar":
        arguments = ["import-reconstruction", str(path), *(["--new-id"] if data.new_id else [])]
        return {"kind": kind, "reconstruction": await _run_howard_test_json_async(*arguments)}

    job = Job(id=str(uuid.uuid4()), kind="reconstruct")
    JOBS[job.id] = job
    _spawn(_run_spherical_reconstruct_job(job, path))
    return {"kind": kind, "job_id": job.id, "name": path.stem}


def _list_localizations() -> list[dict[str, Any]]:
    if not LOCALIZATIONS_DIR.exists():
        return []
    runs: list[dict[str, Any]] = []
    for run_dir in LOCALIZATIONS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        data = _read_json(run_dir / "results.json")
        request = _read_json(run_dir / "request.json") or {}
        progress = _read_json(run_dir / "progress.json")
        job = _run_job(run_dir.name)
        source = data or request
        images = (data or {}).get("images", [])
        if data is not None:
            status, error = "done", None
        elif job is not None and job.status == "running":
            status, error = "running", None
        elif job is not None and job.status == "failed":
            status, error = "failed", job.error
        else:
            status, error = "incomplete", None
        runs.append({
            "run_id": source.get("run_id", run_dir.name),
            "reconstruction_id": source.get("reconstruction_id"),
            "created_at": source.get("created_at"),
            "image_dir": source.get("image_dir"),
            "use_chunking": source.get("use_chunking"),
            "status": status,
            "error": error,
            "progress": progress,
            "image_count": len(images) if data is not None else (progress or {}).get("total", 0),
            "valid_count": sum(1 for img in images if img.get("status") == "ok"),
        })
    runs.sort(key=lambda r: r["created_at"] or "", reverse=True)
    return runs


def _delete_localization(run_id: str) -> None:
    run_dir = (LOCALIZATIONS_DIR / run_id).resolve()
    if run_dir.parent != LOCALIZATIONS_DIR.resolve() or not run_dir.is_dir():
        raise NotFoundException(f"No localization run {run_id}")
    job = _run_job(run_id)
    if job is not None and job.status == "running":
        raise ValueError(f"Localization run {run_id} is still running")
    shutil.rmtree(run_dir)


@delete("/api/localizations/{run_id:str}")
async def delete_localization(run_id: str) -> None:
    await asyncio.to_thread(_delete_localization, run_id)


@get("/api/localizations")
async def list_localizations() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_localizations)


# "Poseless image sets" (Reconstruct tab): a plain sequentially-ordered folder of images with no
# known camera pose (e.g. frames extracted from a video). Registering one here is purely local
# bookkeeping — no placeframe capture session exists yet, just a reference to a server-local
# directory plus a display name, persisted to POSELESS_SETS_INDEX so the table survives a dashboard
# restart. The actual capture upload + synthetic-trajectory reconstruction only happens when
# "Reconstruct" is clicked, via `howard-test reconstruct-poseless` (scripts/src/scripts/howard_test.py).
def _load_poseless_index() -> dict[str, dict[str, Any]]:
    if not POSELESS_SETS_INDEX.exists():
        return {}
    try:
        return json.loads(POSELESS_SETS_INDEX.read_text())
    except json.JSONDecodeError:
        return {}


def _save_poseless_index(index: dict[str, dict[str, Any]]) -> None:
    POSELESS_SETS_DIR.mkdir(parents=True, exist_ok=True)
    POSELESS_SETS_INDEX.write_text(json.dumps(index))


def _scan_poseless_images(path: Path) -> tuple[int, str]:
    images = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in POSELESS_IMAGE_EXTENSIONS]
    if not images:
        raise ValueError(f"No images (.jpg/.jpeg/.png) found in {path}")
    earliest_mtime = min(p.stat().st_mtime for p in images)
    recorded_at = datetime.fromtimestamp(earliest_mtime, tz=timezone.utc).isoformat()
    return len(images), recorded_at


def _register_poseless_set(path_str: str) -> dict[str, Any]:
    path = Path(path_str).expanduser().resolve()
    if not path.is_dir():
        raise NotFoundException(f"Not a directory: {path}")
    image_count, recorded_at = _scan_poseless_images(path)
    entry = {
        "id": str(uuid.uuid4()),
        "name": path.name,
        "path": str(path),
        "image_count": image_count,
        "recorded_at": recorded_at,
    }
    index = _load_poseless_index()
    index[entry["id"]] = entry
    _save_poseless_index(index)
    return entry


@dataclass
class RegisterPoselessSetRequest:
    path: str


@post("/api/poseless-sets")
async def register_poseless_set(data: RegisterPoselessSetRequest) -> dict[str, Any]:
    return await asyncio.to_thread(_register_poseless_set, data.path)


@get("/api/poseless-sets")
async def list_poseless_sets() -> list[dict[str, Any]]:
    entries = list((await asyncio.to_thread(_load_poseless_index)).values())
    entries.sort(key=lambda e: e["recorded_at"], reverse=True)
    return entries


@dataclass
class RenamePoselessSetRequest:
    name: str


def _rename_poseless_set(set_id: str, name: str) -> dict[str, Any]:
    index = _load_poseless_index()
    entry = index.get(set_id)
    if entry is None:
        raise NotFoundException(f"No poseless image set {set_id}")
    entry["name"] = name
    _save_poseless_index(index)
    return entry


@patch("/api/poseless-sets/{set_id:str}")
async def rename_poseless_set(set_id: str, data: RenamePoselessSetRequest) -> dict[str, Any]:
    return await asyncio.to_thread(_rename_poseless_set, set_id, data.name)


@dataclass
class ReconstructRequest:
    capture_id: str
    options_json: str | None = None


@dataclass
class VisualizeRequest:
    reconstruction_id: str


@dataclass
class LocalizeRequest:
    reconstruction_id: str
    image_dir: str
    retrieval_top_k: int | None = None
    ransac_threshold: float | None = None
    use_chunking: bool = True


@dataclass
class SaveTableRequest:
    output_path: str


@dataclass
class SaveImagesRequest:
    output_dir: str


@dataclass
class ExportPosesRequest:
    reconstruction_id: str
    output_path: str


@post("/api/reconstruct")
async def start_reconstruct(data: ReconstructRequest) -> dict[str, str]:
    job = Job(id=str(uuid.uuid4()), kind="reconstruct")
    JOBS[job.id] = job
    _spawn(_run_reconstruct_job(job, data.capture_id, data.options_json))
    return {"job_id": job.id}


@dataclass
class PoselessReconstructRequest:
    focal_length: float
    # None reconstructs every image in the folder; a count thins towards it.
    target_keyframes: int | None = None
    options_json: str | None = None


@post("/api/poseless-sets/{set_id:str}/reconstruct")
async def start_poseless_reconstruct(set_id: str, data: PoselessReconstructRequest) -> dict[str, str]:
    index = await asyncio.to_thread(_load_poseless_index)
    entry = index.get(set_id)
    if entry is None:
        raise NotFoundException(f"No poseless image set {set_id}")
    # A folder's capture is uploaded once and reused, so all its reconstructions nest under one
    # capture. The focal length is baked into that capture's manifest at upload, so a different
    # focal length needs a fresh capture (which then becomes the folder's linked one).
    reuse = entry.get("capture_session_id") if entry.get("focal_length") == data.focal_length else None
    job = Job(id=str(uuid.uuid4()), kind="reconstruct")
    JOBS[job.id] = job
    _spawn(
        _run_poseless_reconstruct_job(
            job, set_id, entry, data.focal_length, data.target_keyframes, data.options_json, reuse
        )
    )
    return {"job_id": job.id}


@post("/api/visualize")
async def start_visualize(data: VisualizeRequest) -> dict[str, str]:
    job = Job(id=str(uuid.uuid4()), kind="visualize", reconstruction_id=data.reconstruction_id)
    JOBS[job.id] = job
    _spawn(_run_visualize_job(job, data.reconstruction_id))
    return {"job_id": job.id}


@post("/api/localize")
async def start_localize(data: LocalizeRequest) -> dict[str, str]:
    # The run id is generated here, up front, rather than left to the CLI to generate — that way
    # the frontend can start polling GET /api/localizations/{run_id}/progress the moment the job
    # id comes back, instead of waiting for the whole (possibly slow, many-image) subprocess to
    # finish and report its own run_id in job.result.
    run_id = str(uuid.uuid4())
    job = Job(id=str(uuid.uuid4()), kind="localize", reconstruction_id=data.reconstruction_id, run_id=run_id)
    JOBS[job.id] = job
    # Recorded before the CLI starts so the run is listed under its reconstruction straight away,
    # with its progress, rather than appearing only once results.json lands.
    await asyncio.to_thread(_write_localize_request, run_id, data)
    _spawn(_run_localize_job(job, data, run_id))
    return {"job_id": job.id, "run_id": run_id}


def _write_localize_request(run_id: str, data: LocalizeRequest) -> None:
    run_dir = LOCALIZATIONS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "request.json").write_text(
        json.dumps({
            "run_id": run_id,
            "reconstruction_id": data.reconstruction_id,
            "image_dir": data.image_dir,
            "use_chunking": data.use_chunking,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    )


def _raise_poll_timeout(reconstruction_id: str | None) -> NoReturn:
    raise TimeoutError(f"Reconstruction {reconstruction_id} did not finish within {RECONSTRUCT_POLL_TIMEOUT_S}s")


async def _poll_reconstruction_until_terminal(job: Job, created: dict[str, Any]) -> None:
    job.reconstruction_id = created["id"]
    job.result = created

    deadline = time.monotonic() + RECONSTRUCT_POLL_TIMEOUT_S
    status = created
    while status["status"] not in ("succeeded", "failed", "cancelled"):
        if time.monotonic() > deadline:
            _raise_poll_timeout(job.reconstruction_id)
        await asyncio.sleep(RECONSTRUCT_POLL_INTERVAL_S)
        # --cache: once the reconstruction succeeds, download and cache its tar locally so
        # the Visualize tab's "Create PNG" doesn't re-download it.
        status = await _run_howard_test_json_async("show", job.reconstruction_id, "--cache")
        job.result = status

    if status["status"] == "succeeded":
        job.status = "succeeded"
    else:
        job.status = "failed"
        job.error = status.get("error") or f"Reconstruction ended as {status['status']}"


async def _run_reconstruct_job(job: Job, capture_id: str, options_json: str | None) -> None:
    try:
        create_args = ["reconstruct", capture_id]
        if options_json:
            create_args += ["--options-json", options_json]
        created = await _run_howard_test_json_async(*create_args)
        await _poll_reconstruction_until_terminal(job, created)
    except Exception as exc:  # subprocess/parse failure, timeout, etc. — surfaced to the poller
        job.status = "failed"
        job.error = str(exc)


def _link_poseless_capture(set_id: str, capture_session_id: str, focal_length: float) -> None:
    index = _load_poseless_index()
    if set_id in index:
        index[set_id]["capture_session_id"] = capture_session_id
        index[set_id]["focal_length"] = focal_length
        _save_poseless_index(index)


async def _run_poseless_reconstruct_job(
    job: Job,
    set_id: str,
    entry: dict[str, Any],
    focal_length: float,
    target_keyframes: int | None,
    options_json: str | None,
    reuse_capture_id: str | None,
) -> None:
    create_args = ["reconstruct-poseless", entry["path"], "--name", entry["name"], "--focal-length", str(focal_length)]
    if target_keyframes is not None:
        create_args += ["--target-keyframes", str(target_keyframes)]
    if options_json:
        create_args += ["--options-json", options_json]
    if reuse_capture_id:
        create_args += ["--capture-id", reuse_capture_id]
    try:
        created = await _run_howard_test_json_async(*create_args)
        if created.get("capture_session_id"):
            await asyncio.to_thread(_link_poseless_capture, set_id, created["capture_session_id"], focal_length)
        await _poll_reconstruction_until_terminal(job, created)
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


async def _run_spherical_reconstruct_job(job: Job, video: Path) -> None:
    try:
        created = await _run_howard_test_json_async("reconstruct-spherical", str(video), "--name", video.stem)
        await _poll_reconstruction_until_terminal(job, created)
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


async def _run_visualize_job(job: Job, reconstruction_id: str) -> None:
    try:
        job.result = await _run_howard_test_json_async("visualize", reconstruction_id)
        job.status = "succeeded"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


async def _run_localize_job(job: Job, data: LocalizeRequest, run_id: str) -> None:
    try:
        args = ["localize", data.reconstruction_id, data.image_dir, "--run-id", run_id]
        if data.retrieval_top_k is not None:
            args += ["--retrieval-top-k", str(data.retrieval_top_k)]
        if data.ransac_threshold is not None:
            args += ["--ransac-threshold", str(data.ransac_threshold)]
        args.append("--use-chunking" if data.use_chunking else "--no-chunking")
        job.result = await _run_howard_test_json_async(*args)
        job.status = "succeeded"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


@get("/api/jobs/{job_id:str}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = JOBS.get(job_id)
    if job is None:
        raise NotFoundException(f"No job {job_id}")
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "reconstruction_id": job.reconstruction_id,
        "run_id": job.run_id,
        "result": job.result,
        "error": job.error,
    }


@get("/api/reconstructions/{reconstruction_id:str}/png")
async def get_png(reconstruction_id: str) -> File:
    path = RECONSTRUCTIONS_DIR / f"{reconstruction_id}.png"
    if not path.exists():
        raise NotFoundException("No PNG cached for this reconstruction yet — run Create PNG first")
    return File(path=path, media_type="image/png")


@get("/api/reconstructions/{reconstruction_id:str}/points")
async def get_points(reconstruction_id: str) -> Response[bytes]:
    # Raw passthrough of `howard-test points`'s binary stdout (count, then flat float32 xyz, then
    # flat uint8 rgb) — see that command's docstring in howard_test.py. The interactive viewer
    # parses this directly with DataView/typed-array views; no JSON round trip either side.
    data = await _run_howard_test_bytes_async("points", reconstruction_id)
    return Response(content=data, media_type="application/octet-stream")


@get("/api/localizations/{run_id:str}")
async def get_localization(run_id: str) -> dict[str, Any]:
    path = LOCALIZATIONS_DIR / run_id / "results.json"
    if not path.exists():
        raise NotFoundException(f"No localization run {run_id}")
    return json.loads(path.read_text())


@get("/api/localizations/{run_id:str}/progress")
async def get_localization_progress(run_id: str) -> dict[str, Any]:
    # The CLI writes this file the instant it starts (completed=0, total=<image count>) and
    # rewrites it after each image, so it's readable well before results.json exists. If the
    # subprocess hasn't even created the run directory yet (a brief window right after the job
    # is spawned), report an empty/unknown progress rather than 404 — the frontend treats that as
    # "still starting" instead of an error.
    path = LOCALIZATIONS_DIR / run_id / "progress.json"
    if not path.exists():
        return {"completed": 0, "total": 0}
    return json.loads(path.read_text())


@post("/api/localizations/{run_id:str}/save-table")
async def save_localization_table(run_id: str, data: SaveTableRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("localize-save-table", run_id, data.output_path)


@post("/api/localizations/{run_id:str}/save-images")
async def save_localization_images(run_id: str, data: SaveImagesRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("localize-save-images", run_id, data.output_dir)


@post("/api/tools/export-poses")
async def export_poses(data: ExportPosesRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("export-poses", data.reconstruction_id, data.output_path)


@dataclass
class ExportZipRequest:
    output_path: str


@post("/api/reconstructions/{reconstruction_id:str}/export-zip")
async def export_reconstruction_zip(reconstruction_id: str, data: ExportZipRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("export-zip", reconstruction_id, data.output_path)


@dataclass
class ScreenshotRequest:
    plot_title: str
    image_base64: str
    localization_id: str | None = None


_UNSAFE_TITLE_CHARS = re.compile(r"[^A-Za-z0-9._ -]")
_CAPTURE_FILENAME = re.compile(r"^(?P<title>.+)_capture(?P<n>\d+)\.png$")


def _sanitize_title(title: str) -> str:
    cleaned = _UNSAFE_TITLE_CHARS.sub("_", title.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "reconstruction"


def _next_capture_path(folder: Path, prefix: str) -> Path:
    numbers = [int(m["n"]) for f in folder.glob(f"{prefix}_capture*.png") if (m := _CAPTURE_FILENAME.match(f.name))]
    next_n = max(numbers) + 1 if numbers else 0
    return folder / f"{prefix}_capture{next_n}.png"


@post("/api/screenshots")
async def save_screenshot(data: ScreenshotRequest) -> dict[str, str]:
    # All viewer captures go to one flat data/visualizations/ folder now, prefixed by the first 4
    # characters of the identifying id — the localization run id when viewing a localization,
    # otherwise the plot title (which defaults to the reconstruction id) for a plain reconstruction
    # view. 4 chars isn't collision-proof, but this is a scratch/inspection folder, not a durable
    # store — see dashboard/project.md if this needs to become collision-safe later.
    identifier = data.localization_id or data.plot_title
    prefix = _sanitize_title(identifier)[:4]
    VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = _next_capture_path(VISUALIZATIONS_DIR, prefix)
    path.write_bytes(base64.b64decode(data.image_base64))
    return {"path": str(path)}


def _exception_handler(_: Request[Any, Any, Any], exc: Exception) -> Response[dict[str, str]]:
    return Response({"detail": str(exc)}, status_code=500)


cors_config = CORSConfig(allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"])

app = Litestar(
    route_handlers=[
        browse_directories,
        list_captures,
        list_reconstructions,
        delete_reconstruction,
        delete_capture,
        rename_capture,
        import_reconstruction,
        import_path,
        list_localizations,
        delete_localization,
        register_poseless_set,
        list_poseless_sets,
        rename_poseless_set,
        start_reconstruct,
        start_poseless_reconstruct,
        start_visualize,
        start_localize,
        get_job,
        get_png,
        get_points,
        get_localization,
        get_localization_progress,
        save_localization_table,
        save_localization_images,
        export_poses,
        export_reconstruction_zip,
        save_screenshot,
    ],
    cors_config=cors_config,
    exception_handlers={RuntimeError: _exception_handler, ValueError: _exception_handler},
)
